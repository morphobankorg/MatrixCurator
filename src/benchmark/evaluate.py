import asyncio
from src.modules.agent.graph import agent_graph
from src.config.main import settings
import uuid

async def run_benchmark():
    print("Running benchmark...")
    # In a real scenario, we would load a dataset from Langfuse or local files
    # and iterate over it.
    
    sample_context = "Character 1: Eye color. 0: blue, 1: brown."
    
    config = {
        "configurable": {
            "thread_id": str(uuid.uuid4()),
            "model_provider": settings.DEFAULT_MODEL,
            "fallback_model": settings.FALLBACK_MODEL,
            "user_id": "benchmark_user"
        }
    }
    
    initial_state = {
        "character_index": 1,
        "context": sample_context,
        "current_model": settings.DEFAULT_MODEL,
        "attempts": 0,
        "errors": []
    }
    
    result = await agent_graph.ainvoke(initial_state, config)
    print("Benchmark result:", result.get("extracted_data"))
    print("Evaluation score:", result.get("evaluation_score"))

if __name__ == "__main__":
    asyncio.run(run_benchmark())
