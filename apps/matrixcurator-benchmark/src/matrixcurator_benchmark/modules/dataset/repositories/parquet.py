# src/benchmark/modules/dataset/repositories/parquet.py
import pyarrow.parquet as pq
import pyarrow as pa
from typing import List, Dict, Any

def read_documents(file_path: str) -> List[Dict[str, Any]]:
    return pq.read_table(file_path).to_pylist()

def write_documents(records: List[Dict[str, Any]], file_path: str) -> None:
    pq.write_table(pa.Table.from_pylist(records), file_path)

def read_character_states(file_path: str) -> List[Dict[str, Any]]:
    return pq.read_table(file_path).to_pylist()
