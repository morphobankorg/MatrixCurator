import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import structlog
import numpy as np
import random

import dspy
from dspy.teleprompt import MIPROv2

from matrixcurator.integrations.dspy import (
    configure_dspy,
    ExtractionModule,
    EvaluationModule,
)
from matrixcurator.config.main import settings

logger = structlog.get_logger(__name__)

# Global evaluator LM initialized explicitly
from matrixcurator.integrations.dspy import MCPAwareLM
prompt_lm = MCPAwareLM("gemini/gemini-3.1-pro-preview")

# Globally instantiate evaluation module once to avoid repeated disk I/O and initialization overhead
with dspy.context(lm=prompt_lm):
    GLOBAL_EVALUATOR = EvaluationModule(model_name="gemini/gemini-3.1-pro-preview")


def extraction_metric(
    example: dspy.Example, pred: dspy.Prediction, trace=None
) -> float:
    """
    DSPy metric function that uses our existing LLM-as-a-judge signature
    to evaluate the prediction against the ground truth.
    """
    # Create the structured data dict expected by the prompt
    extracted_data_dict = {
        "character": getattr(pred, "character_name", ""),
        "states": getattr(pred, "states", []),
        "expected_character": {
            "index": example.character_index,
            "name": example.character.get("name", ""),
        },
        "expected_states": example.states,
    }

    with dspy.context(lm=prompt_lm):
        result = GLOBAL_EVALUATOR(
            document_text=example.document_text,
            extracted_data=extracted_data_dict,
        )

    # Return normalized score 0.0-1.0
    return float(getattr(result, "score", 0)) / 10.0


def load_examples() -> list[dspy.Example]:
    """Loads parquet data and converts to dspy.Example objects."""
    data_dir = Path("apps/matrixcurator-benchmark/src/matrixcurator_benchmark/data")
    docs_path = data_dir / "documents.parquet"
    chars_path = data_dir / "character_states.parquet"

    if not docs_path.exists() or not chars_path.exists():
        raise FileNotFoundError("Benchmark parquet files not found.")

    df_docs = pd.read_parquet(docs_path)
    df_chars = pd.read_parquet(chars_path)

    # We assume df_docs has 'id' and 'text' dict
    # We assume df_chars has 'document_id', 'character', 'states'

    examples = []

    for _, char_row in df_chars.iterrows():
        doc_id = char_row.get("document_id") or char_row.get("id")

        # Find matching doc
        doc_match = df_docs[(df_docs["id"] == doc_id) | (df_docs.get("document_id", "") == doc_id)]
        if doc_match.empty:
            continue

        doc_row = doc_match.iloc[0]
        
        pre_parsed_text = doc_row.get("text")
        if isinstance(pre_parsed_text, str):
            try:
                parses = json.loads(pre_parsed_text)
            except Exception:
                parses = []
        elif isinstance(pre_parsed_text, (list, tuple)):
            parses = list(pre_parsed_text)
        else:
            parses = []
            
        # Extract target pages for the character
        target_pages = []
        raw_pages = char_row.get("pages")
        if isinstance(raw_pages, np.ndarray):
            target_pages = raw_pages.tolist()
        elif isinstance(raw_pages, str):
            try:
                target_pages = json.loads(raw_pages)
            except Exception:
                pass
        elif isinstance(raw_pages, list):
            target_pages = raw_pages
        
        doc_text = ""
        preferred_parsers = ["docling", "pymupdf", "docx", "txt"]
        for preferred in preferred_parsers:
            for parse_obj in parses:
                if parse_obj.get("parser") == preferred:
                    pages = parse_obj.get("pages", [])
                    filtered_pages = []
                    for p in pages:
                        if not isinstance(p, dict):
                            continue
                        # Filter by target pages if specified
                        if target_pages:
                            if p.get("page") in target_pages:
                                filtered_pages.append(str(p.get("content", "")))
                        else:
                            filtered_pages.append(str(p.get("content", "")))
                    doc_text = "\n\n".join(filtered_pages)
                    break
            if doc_text:
                break

        char_data = char_row["character"]
        if isinstance(char_data, str):
            try:
                char_data = json.loads(char_data)
            except Exception:
                char_data = {}
        char_idx = char_data.get("index", 1)

        states_data = char_row.get("states", [])
        if isinstance(states_data, np.ndarray):
            states_data = states_data.tolist()
        elif isinstance(states_data, str):
            try:
                states_data = json.loads(states_data)
            except Exception:
                states_data = []

        example = dspy.Example(
            document_text=doc_text,
            character_index=char_idx,
            previous_errors=None,
            character=char_data,
            states=states_data,
            document_id=doc_id,
        ).with_inputs(
            "document_text", "character_index", "previous_errors"
        )

        examples.append(example)

    return examples


MODELS_TO_COMPILE = [
    "gemini/gemini-3.1-flash-lite",
    "gemini/gemini-3.5-flash",
    "gemini/gemini-2.5-pro",
    "gemini/gemini-2.5-flash",
    "gemini/gemini-3.1-pro-preview",
    "gemini/gemma-4-31b-it",
    "ollama/qwen3.6:35b"
]


def main():
    load_dotenv()
    logger.info("Starting DSPy states compilation process")

    logger.info("Loading datasets...")
    dataset = load_examples()
    logger.info("Loaded total examples", count=len(dataset))

    if not dataset:
        logger.error("No examples loaded. Exiting.")
        return

    MAX_TOTAL_EXAMPLES = settings.max_examples
    doc_ids = list(set(ex.document_id for ex in dataset))
    examples_per_doc = max(1, MAX_TOTAL_EXAMPLES // len(doc_ids))
    
    downsampled_dataset = []
    random.seed(42)
    for doc_id in doc_ids:
        doc_examples = [ex for ex in dataset if ex.document_id == doc_id]
        if len(doc_examples) > examples_per_doc:
            downsampled_dataset.extend(random.sample(doc_examples, examples_per_doc))
        else:
            downsampled_dataset.extend(doc_examples)
            
    dataset = downsampled_dataset
    logger.info(
        f"Downsampled dataset to {len(dataset)} examples for optimization speed "
        f"(approx {examples_per_doc} per doc across {len(doc_ids)} docs)"
    )

    # Simple split
    split_idx = int(len(dataset) * 0.8)
    trainset = dataset[:split_idx]
    valset = dataset[split_idx:]

    logger.info("Dataset split", trainset_size=len(trainset), valset_size=len(valset))

    states_dir = Path("packages/matrixcurator/src/matrixcurator/data/states")
    states_dir.mkdir(parents=True, exist_ok=True)

    for model_name in MODELS_TO_COMPILE:
        clean_name = model_name.split("/")[-1].replace(":", "-") + ".json"
        output_path = states_dir / clean_name

        if output_path.exists() and not settings.force_recompile:
            logger.info("states already exist. Skipping compilation.", model=model_name, path=str(output_path))
            continue

        logger.info(f"Instantiating DSPy student LM for: {model_name}")
        # Initialize isolated student LM without globally polluting config
        task_lm = MCPAwareLM(model_name)
        student = ExtractionModule(model_name=model_name)

        num_threads = settings.dspy_num_threads
        
        # Default to "none" to strictly respect minibatch settings, preventing DSPy from
        # evaluating all 105 examples concurrently and exhausting the Rate Limiter queue
        auto_mode = settings.dspy_auto

        logger.info("Configuring Optimizer (MIPROv2)...")
        mipro_kwargs = {
            "metric": extraction_metric,
            "auto": auto_mode,  # Adjust depending on budget/time
            "num_threads": num_threads,
            "prompt_model": prompt_lm,
            "task_model": task_lm,
        }
        if auto_mode is None:
            # Set a sane default of 3 candidates when manual compiling
            mipro_kwargs["num_candidates"] = settings.num_candidates
            
        teleprompter = MIPROv2(**mipro_kwargs)

        logger.info("Compiling states... This will take time.", model=model_name)
        
        compile_kwargs = {
            "trainset": trainset,
            "valset": valset,
            "minibatch_size": min(settings.minibatch_size, len(valset)) if valset else settings.minibatch_size,  # Configurable
            "minibatch": True,
            "max_bootstrapped_demos": min(settings.max_bootstrapped_demos, len(trainset)),
            "max_labeled_demos": min(settings.max_labeled_demos, len(trainset)),
        }
        
        # If auto is None, we must specify num_trials
        if auto_mode is None:
            compile_kwargs["num_trials"] = settings.num_trials
            
        print("RUNTIME NUM CANDIDATES:", settings.num_candidates)
        print("RUNTIME NUM TRIALS:", settings.num_trials)
        print("RUNTIME MAX EXAMPLES:", settings.max_examples)
            
        # Use isolated context for student compilation
        with dspy.context(lm=task_lm):
            compiled_student = teleprompter.compile(
                student,
                **compile_kwargs
            )

        logger.info(f"Saving compiled states to {output_path}...")
        compiled_student.save(str(output_path))
        logger.info("Completed compilation for model", model=model_name)
    
    logger.info("All compilations done!")


if __name__ == "__main__":
    main()
