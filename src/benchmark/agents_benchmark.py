# src/benchmark/agents_benchmark.py
import os
import json
import pandas as pd
from typing import Any
from lume import structlog

from matrixcurator.config.main import (
    settings,
    OrchestrationStrategy,
    IntelligenceStrategy,
    ContextStrategy,
)
from matrixcurator.modules.graph import build_graph
from .confbenchmark import setup

logger = structlog.get_logger(__name__)


async def agent_task(*, item: Any, df_docs: pd.DataFrame, **kwargs) -> str:
    input_data = item.input
    document_id = input_data.get("document_id")
    character_index = input_data.get("character_index", 1)
    pages = input_data.get("pages", [1])

    # Retrieve file bytes from dataframe
    doc_row = df_docs[df_docs["id"] == document_id]
    if doc_row.empty:
        return json.dumps({"error": f"Document {document_id} not found in parquet"})

    file_bytes = doc_row.iloc[0]["file_bytes"]
    filename = doc_row.iloc[0].get("filename", f"doc_{document_id}.pdf")

    # Initialize state
    initial_state = {
        "document": {
            "file_bytes": file_bytes,
            "filename": filename,
            "status": "pending",
            "inferred_pages": pages,  # Use the explicit pages from the dataset
            "total_characters": character_index,
            "discovery_confidence": 0.99,
        },
        "characters": {
            str(character_index): [
                {
                    "character": {"index": character_index, "name": ""},
                    "states": [],
                    "status": "pending",
                }
            ]
        },
        "current_focus": str(character_index),
    }

    graph = build_graph()

    final_state = await graph.ainvoke(
        initial_state, config={"configurable": {"thread_id": f"benchmark-{item.id}"}}
    )

    # Extract the resulting states for the requested character
    attempts = final_state.get("characters", {}).get(str(character_index), [])
    if attempts:
        latest = attempts[-1]
        extracted_data = {
            "character": latest.get("character"),
            "states": latest.get("states"),
        }
        return json.dumps(extracted_data)

    return "{}"


def run_agents_benchmark():
    langfuse, dataset = setup()

    data_dir = os.path.join(os.path.dirname(__file__), "data")
    docs_path = os.path.join(data_dir, "documents.parquet")
    logger.info("Loading documents parquet", path=docs_path)
    df_docs = pd.read_parquet(docs_path)

    permutations = [
        (OrchestrationStrategy.STATIC_ROUTING, IntelligenceStrategy.PROMPT_ENGINEERING),
        (
            OrchestrationStrategy.STATIC_ROUTING,
            IntelligenceStrategy.PROGRAMMATIC_OPTIMIZATION,
        ),
        (
            OrchestrationStrategy.DYNAMIC_ROUTING,
            IntelligenceStrategy.PROMPT_ENGINEERING,
        ),
        (
            OrchestrationStrategy.DYNAMIC_ROUTING,
            IntelligenceStrategy.PROGRAMMATIC_OPTIMIZATION,
        ),
    ]

    def process_permutation(routing, intelligence):
        run_name = f"Agent-{routing.value}-{intelligence.value}"
        logger.info(
            "Running Agent Benchmark",
            routing=routing.value,
            intelligence=intelligence.value,
        )

        # Override settings for the duration of this run
        settings.orchestration_strategy = routing
        settings.intelligence_strategy = intelligence

        # We always use FULL_CONTEXT for agents benchmark to isolate orchestration/intelligence from retrieval issues
        settings.context_strategy = ContextStrategy.FULL_CONTEXT

        dataset.run_experiment(
            name=run_name,
            description=f"Agent Benchmark with Routing={routing.value}, Intelligence={intelligence.value}",
            task=lambda *, item, **kwargs: agent_task(item=item, df_docs=df_docs),
        )

    for routing, intelligence in permutations:
        process_permutation(routing, intelligence)

    langfuse.flush()
    logger.info("Agents Benchmark completed")


if __name__ == "__main__":
    run_agents_benchmark()
