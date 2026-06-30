import asyncio
from typing import Any

from langfuse import Langfuse
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _sync_create_dataset_item(client: Langfuse, dataset_name: str, item: Any) -> None:
    """Synchronous function to create or upsert a dataset item via Langfuse client."""
    # Ensure item has id, input, expected_output, and metadata
    client.create_dataset_item(
        dataset_name=dataset_name,
        input=item.get("input", {}),
        expected_output=item.get("expected_output", {}),
        metadata=item.get("metadata", {}),
        id=item.get("id"),
    )


async def upsert_dataset_item(client: Langfuse, dataset_name: str, item: Any) -> None:
    """Asynchronously create or upsert a dataset item with retry logic."""
    await asyncio.to_thread(_sync_create_dataset_item, client, dataset_name, item)
