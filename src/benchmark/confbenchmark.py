# src/benchmark/confbenchmark.py
import os
import json
import pandas as pd
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.api.commons import ScoreConfigDataType, ConfigCategory
from python_logging import get_logger

logger = get_logger(__name__)

# Unstable imports for Managed Evaluator API
from langfuse.api.unstable.commons import (
    EvaluatorModelConfig,
    EvaluatorOutputDataType,
    EvaluatorOutputDefinition_Categorical,
    EvaluatorOutputFieldDefinition,
    EvaluationRuleMapping,
    EvaluationRuleMappingSource,
    EvaluationRuleTarget,
    EvaluatorScope
)
from langfuse.api.unstable.evaluation_rules import (
    CreateLlmAsJudgeEvaluationRuleRequest,
    LlmAsJudgeEvaluationRuleEvaluatorReference
)
from langfuse.api.unstable.evaluators import CreateEvaluatorRequest_LlmAsJudge

def sync_to_langfuse(langfuse: Langfuse):
    """
    Reads local parquet datasets and syncs them to Langfuse.
    """
    dataset_name = "default"
    logger.info("Creating or getting dataset", dataset_name=dataset_name)
    langfuse.create_dataset(
        name=dataset_name,
        description="Dataset containing morphological character states and their source document text.",
    )
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    docs_path = os.path.join(data_dir, "documents.parquet")
    chars_path = os.path.join(data_dir, "character_states.parquet")
    
    if not os.path.exists(docs_path) or not os.path.exists(chars_path):
        logger.error("Parquet files not found", data_dir=data_dir)
        return
        
    logger.info("Reading parquet files")
    df_docs = pd.read_parquet(docs_path)
    df_chars = pd.read_parquet(chars_path)
    
    if 'document_id' in df_chars.columns and 'id' in df_docs.columns:
        merged_df = df_chars.merge(df_docs, left_on='document_id', right_on='id', suffixes=('', '_doc'))
    else:
        merged_df = df_chars
        
    merged_df = merged_df.head(10)
        
    logger.info("Uploading items to Langfuse")
    for idx, row in merged_df.iterrows():
        character_data = row.get("character", {})
        if isinstance(character_data, str):
            try:
                character_data = json.loads(character_data)
            except:
                character_data = {}
                
        char_index = character_data.get("index", 1)
        
        states_data = row.get("states", [])
        if isinstance(states_data, str):
            try:
                states_data = json.loads(states_data)
            except:
                states_data = []
        elif hasattr(states_data, 'tolist'):
            states_data = states_data.tolist()
            
        pages = row.get("pages", [1])
        if isinstance(pages, str):
            pages = [int(p) for p in pages.split("-")] if "-" in pages else [int(pages)]
        elif hasattr(pages, 'tolist'):
            pages = pages.tolist()
            
        input_data = {
            "character_index": char_index,
            "document_id": str(row.get("document_id", "unknown")),
            "pages": pages
        }
        
        character_data["states"] = states_data
        
        expected_output = json.dumps({
            "character": character_data
        })
        
        item_name = f"Doc-{input_data['document_id']}-Char-{input_data['character_index']}"
        
        langfuse.create_dataset_item(
            dataset_name=dataset_name,
            input=input_data,
            expected_output=expected_output,
            metadata={"source_row_index": idx, "name": item_name}
        )
        logger.debug("Uploaded item", item_index=idx + 1, total_items=len(merged_df))
        
    logger.info("Dataset sync complete")

def setup_evaluators(langfuse: Langfuse):
    """
    Configure the Score Config, Managed Evaluators, and Evaluation Rules via the Langfuse API.
    """
    logger.info("Setting up Langfuse Evaluators and Score Config")
    
    # 1. Create the Score Config
    # Check if we should create it
    # For idempotency, we can just upsert/create. Langfuse usually handles updates gracefully by id or name if we query it first.
    # We will just list and check if exists, otherwise create
    
    try:
        score_configs = langfuse.api.score_configs.get()
        config_names = [sc.name for sc in score_configs.data]
    except Exception as e:
        config_names = []
        
    if "Semantic Recall" not in config_names:
        logger.info("Creating score config", config_name="Semantic Recall")
        langfuse.api.score_configs.create(
            name="Semantic Recall",
            data_type=ScoreConfigDataType.CATEGORICAL,
            categories=[
                ConfigCategory(label="Complete Recall", value=1.0),
                ConfigCategory(label="Recall Failure", value=0.0),
                ConfigCategory(label="Partial Recall", value=0.5),
                ConfigCategory(label="Semantic Corruption", value=0.25),
                ConfigCategory(label="Low Context Precision", value=0.1)
            ],
            description="Score to measure semantic entailment using LLM-as-a-judge."
        )
    else:
        logger.info("Score config already exists", config_name="Semantic Recall")

    # 2. Create the Evaluator
    evaluator_name = "Semantic Recall"
    logger.info("Creating or upserting Managed Evaluator", evaluator_name=evaluator_name)
    
    prompt_text = (
        "You are an expert morphological analyst. Your task is to evaluate if the semantic information from the Expected Output is present within the raw text of the Extracted Output.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. The Expected Output is formatted as JSON, but the Extracted Output is raw unstructured text parsed from a PDF/DOCX.\n"
        "2. DO NOT penalize the Extracted Output for lacking JSON formatting, brackets, or exact structural matching.\n"
        "3. Focus purely on semantic entailment (checking if the expected character name, index, and state names/indices exist within the text).\n\n"
        "Expected Output:\n"
        "{{expected_output}}\n\n"
        "Extracted Output:\n"
        "{{output}}\n\n"
        "Assign the most appropriate category based on the precision and recall of the expected morphological character information within the extracted text.\n"
    )

    try:
        eval_provider = os.getenv("LANGFUSE_EVAL_PROVIDER", "google")
        eval_model = os.getenv("LANGFUSE_EVAL_MODEL", "gemini-3.5-flash")

        # Create Evaluator. If it already exists, Langfuse automatically increments version.
        evaluator = langfuse.api.unstable.evaluators.create(
            request=CreateEvaluatorRequest_LlmAsJudge(
                name=evaluator_name,
                prompt=prompt_text,
                output_definition=EvaluatorOutputDefinition_Categorical(
                    data_type=EvaluatorOutputDataType.CATEGORICAL,
                    categories=[
                        {"label": "Complete Recall", "value": 1.0},
                        {"label": "Recall Failure", "value": 0.0},
                        {"label": "Partial Recall", "value": 0.5},
                        {"label": "Semantic Corruption", "value": 0.25},
                        {"label": "Low Context Precision", "value": 0.1}
                    ],
                    reasoning=EvaluatorOutputFieldDefinition(
                        description="Explain why this category was assigned based on the semantic match."
                    ),
                    score={
                        "description": "Select the best category label from the defined score config.",
                        "categories": [
                            "Complete Recall",
                            "Recall Failure",
                            "Partial Recall",
                            "Semantic Corruption",
                            "Low Context Precision"
                        ],
                        "should_allow_multiple_matches": False
                    }
                ),
                model_config_=EvaluatorModelConfig(
                    provider=eval_provider,
                    model=eval_model
                )
            )
        )
        logger.info("Evaluator created or updated", evaluator_id=evaluator.id)
        
        # 3. Create the Evaluation Rule
        # We link the evaluator to traces matching our benchmark runner names
        trace_names = ["Parser-Docling-Run", "Parser-PyMuPDF-Run", "Parser-DOCX-Run", "Parser-TXT-Run", "Supabase-RAG-Run"]
        
        # We need to fetch existing rules to avoid duplicates.
        existing_rules = langfuse.api.unstable.evaluation_rules.list().data
        existing_rule_names = [rule.name for rule in existing_rules]
        
        # Fetch dataset ID for filtering
        dataset = langfuse.get_dataset("default")
        dataset_id = dataset.id

        rule_name = "Semantic Recall"
        if rule_name not in existing_rule_names:
            logger.info("Creating Evaluation Rule", rule_name=rule_name)
            # Create rule triggering for experiments on this dataset
            langfuse.api.unstable.evaluation_rules.create(
                request=CreateLlmAsJudgeEvaluationRuleRequest(
                    name=rule_name,
                    evaluator=LlmAsJudgeEvaluationRuleEvaluatorReference(
                        name=evaluator_name,
                        scope=EvaluatorScope.PROJECT
                    ),
                    target=EvaluationRuleTarget.EXPERIMENT,
                    enabled=True,
                    sampling=1.0,
                    filter=[
                        {
                            "type": "stringOptions",
                            "column": "datasetId",
                            "operator": "any of",
                            "value": [dataset_id]
                        }
                    ],
                    mapping=[
                        EvaluationRuleMapping(
                            variable="output",
                            source=EvaluationRuleMappingSource.OUTPUT
                        ),
                        EvaluationRuleMapping(
                            variable="expected_output",
                            source=EvaluationRuleMappingSource.EXPECTED_OUTPUT
                        )
                    ]
                )
            )
        else:
            logger.info("Evaluation Rule already exists", rule_name=rule_name)
            
    except Exception as e:
        error_str = str(e)
        logger.warning("Failed to setup Managed Evaluator or Rules via API", error=error_str)
        if "422" in error_str and "No valid LLM model found" in error_str:
            logger.warning(
                "ACTION REQUIRED: Langfuse Cloud rejected the Evaluator Model configuration. "
                "You must log into your Langfuse project dashboard, go to Settings > Model Providers, "
                "and configure the API credentials for your chosen provider. "
                "Ensure that the provider and model match the values set in LANGFUSE_EVAL_PROVIDER "
                "and LANGFUSE_EVAL_MODEL (defaults: 'google' and 'gemini-3.5-flash')."
            )

def setup():
    """
    Main initialization entry point for benchmarks.
    Syncs dataset and sets up Evaluators.
    """
    load_dotenv()
    import logging
    logging.getLogger("langfuse").setLevel(logging.ERROR)
    langfuse = Langfuse()
    
    sync_to_langfuse(langfuse)
    setup_evaluators(langfuse)
    
    langfuse.flush()
    dataset = langfuse.get_dataset("default")
    return langfuse, dataset
