# src/benchmark/benchmark_agents.py
import json
import pandas as pd
from lume import structlog

from src.benchmark.core.decorators import benchmark, parametrize, fixture
from src.benchmark.core.exceptions import FailBenchmark

from matrixcurator.config.main import (
    settings,
    OrchestrationStrategy,
    IntelligenceStrategy,
    ContextStrategy,
)
from matrixcurator.modules.graph import build_graph

logger = structlog.get_logger(__name__)

PERMUTATIONS = [
    (OrchestrationStrategy.STATIC_ROUTING, IntelligenceStrategy.PROMPT_ENGINEERING),
    (
        OrchestrationStrategy.STATIC_ROUTING,
        IntelligenceStrategy.PROGRAMMATIC_OPTIMIZATION,
    ),
    (OrchestrationStrategy.DYNAMIC_ROUTING, IntelligenceStrategy.PROMPT_ENGINEERING),
    (
        OrchestrationStrategy.DYNAMIC_ROUTING,
        IntelligenceStrategy.PROGRAMMATIC_OPTIMIZATION,
    ),
]


@fixture(scope="session")
def docs_dict(df_docs: pd.DataFrame):
    if "id" in df_docs.columns:
        return df_docs.set_index("id").to_dict(orient="index")
    return {}


@benchmark(dataset_name="character_states")
@parametrize("routing, intelligence", PERMUTATIONS)
async def benchmark_agents(
    dataset_item, routing, intelligence, docs_dict, langfuse_trace
):
    from matrixcurator.config.main import (
        orchestration_strategy_var,
        intelligence_strategy_var,
        context_strategy_var,
    )
    
    # Override settings for the duration of this run using ContextVar
    orchestration_strategy_var.set(routing)
    intelligence_strategy_var.set(intelligence)
    context_strategy_var.set(ContextStrategy.FULL_CONTEXT)

    input_data = dataset_item.input
    document_id = input_data.get("document_id")
    character_index = input_data.get("character_index", 1)
    pages = input_data.get("pages", [1])

    doc_row = docs_dict.get(document_id)
    if not doc_row:
        raise FailBenchmark(f"Document {document_id} not found in parquet data")

    file_bytes = doc_row.get("file_bytes")
    filename = doc_row.get("filename", f"doc_{document_id}.pdf")

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
        initial_state,
        config={"configurable": {"thread_id": f"benchmark-{dataset_item.id}"}},
    )

    # Extract the resulting states for the requested character
    attempts = final_state.get("characters", {}).get(str(character_index), [])
    if attempts:
        latest = attempts[-1]
        extracted_data = {
            "character": latest.get("character"),
            "states": latest.get("states"),
        }
        langfuse_trace(json.dumps(extracted_data))
    else:
        langfuse_trace("{}")
