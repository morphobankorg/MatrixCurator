# src/benchmark/retrieval_benchmark.py
from typing import Any
from python_logging import get_logger
from matrixcurator.modules.retrieval.services import retrieve_context
from .confbenchmark import setup

logger = get_logger(__name__)

# Using Langfuse dataset runner
async def rag_task(*, item: Any, **kwargs) -> str:
    input_data = item.input
    character_index = input_data.get("character_index", 1)
    
    # We construct a query
    query = f"Character {character_index}"
    
    # Optional filtering by document_id if supported
    document_id = input_data.get("document_id")
    
    # Retrieve context from Supabase vector store
    retrieved_context = await retrieve_context(query=query, document_id=document_id)
    
    return retrieved_context


def run_retrieval_benchmark():
    langfuse, dataset = setup()
    
    logger.info("Running Supabase RAG Benchmark")
    
    dataset.run_experiment(
        name="Supabase-RAG-Run",
        description="Retrieval Benchmark for Supabase RAG",
        task=rag_task
    )
    
    langfuse.flush()
    logger.info("Retrieval Benchmark completed")

if __name__ == "__main__":
    run_retrieval_benchmark()
