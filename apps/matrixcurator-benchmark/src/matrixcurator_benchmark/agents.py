import json
import pandas as pd
import structlog
from typing import Any, Dict
import functools

from matrixcurator_benchmark.services import run_dataset_benchmark
from matrixcurator_benchmark.exceptions import FailBenchmark

from matrixcurator.config.main import (
    settings,
    OrchestrationStrategy,
    IntelligenceStrategy,
    ContextStrategy,
    orchestration_strategy_var,
    intelligence_strategy_var,
    context_strategy_var,
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


async def agent_task(
    *, 
    item: Any, 
    routing: str, 
    intelligence: str, 
    docs_dict: Dict[str, Any],
    **kwargs
) -> str:
    # Override settings for the duration of this run using ContextVar
    orchestration_strategy_var.set(routing)
    intelligence_strategy_var.set(intelligence)
    context_strategy_var.set(ContextStrategy.FULL_CONTEXT)

    input_data = item.input
    
    document_id = None
    character_index = 1
    pages = None
    
    if isinstance(input_data, dict):
        document_id = input_data.get("document_id")
        character_index = input_data.get("character_index", 1)
        pages = input_data.get("pages")
    elif hasattr(input_data, "document_id"):
        document_id = getattr(input_data, "document_id", None)
        character_index = getattr(input_data, "character_index", 1)
        pages = getattr(input_data, "pages", None)
    elif isinstance(input_data, str):
        try:
            parsed = json.loads(input_data)
            if isinstance(parsed, dict):
                document_id = parsed.get("document_id")
                character_index = parsed.get("character_index", 1)
                pages = parsed.get("pages")
        except Exception:
            pass

    doc_row = docs_dict.get(document_id)
    if not doc_row:
        raise ValueError(f"Document {document_id} not found in parquet data")

    if not pages or (hasattr(pages, "__len__") and len(pages) == 0):
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
            
        all_pages = set()
        if not isinstance(parses, list):
            if parses:
                parses = [parses]
            else:
                parses = []
                
        for parse_obj in parses:
            parsed_pages = parse_obj.get("pages") or []
            for pg in parsed_pages:
                if isinstance(pg, dict) and pg.get("page") is not None:
                    all_pages.add(int(pg.get("page")))
        
        if all_pages:
            pages = sorted(list(all_pages))
        else:
            pages = [1]

    file_bytes = doc_row.get("file_bytes")
    filename = doc_row.get("filename", f"doc_{document_id}.pdf")

    initial_state = {
        "document": {
            "file_bytes": file_bytes,
            "filename": filename,
            "status": "pending",
            "inferred_pages": pages,
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
        config={"configurable": {"thread_id": f"benchmark-{getattr(item, 'id', 'unknown')}"}},
    )

    attempts = final_state.get("characters", {}).get(str(character_index), [])
    if attempts:
        latest = attempts[-1]
        extracted_data = {
            "character": latest.get("character"),
            "states": latest.get("states"),
        }
        return json.dumps(extracted_data)
    else:
        return "{}"


async def run_agents_benchmarks(limit: int, workers: int, docs_dict: Dict[str, Any]) -> None:
    for routing, intelligence in PERMUTATIONS:
        run_name = f"benchmark_agent_{routing.value}_{intelligence.value}"
        await run_dataset_benchmark(
            dataset_name="character_states",
            run_name=run_name,
            task_fn=functools.partial(agent_task, routing=routing, intelligence=intelligence, docs_dict=docs_dict),
            limit=limit,
            workers=workers
        )
