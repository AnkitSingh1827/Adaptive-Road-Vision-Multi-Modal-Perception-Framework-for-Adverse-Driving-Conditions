"""
High-Performance JSON and JSONL Streaming Parser for Large Scale Dataset Ingestion.
Enables streaming iteration over large JSON/JSONL annotations without memory exhaustion.
"""

from pathlib import Path
from typing import Generator, Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


def stream_jsonl(file_path: Path) -> Generator[Dict[str, Any], None, None]:
    """
    Yields parsed JSON objects line-by-line from a JSONL file.
    Skips corrupted or empty lines gracefully with logging.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"JSONL file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                yield json.loads(line_str)
            except json.JSONDecodeError as e:
                logger.warning("Failed to decode JSON at %s:%d: %s", path.name, line_idx, e)
                continue


def read_json_or_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Automatically detects whether a file is standard JSON or JSONL and parses into list.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return list(stream_jsonl(path))
    elif suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                return []
    else:
        raise ValueError(f"Unsupported annotation format: {suffix}. Expected .json or .jsonl")


def write_jsonl(records: List[Dict[str, Any]], output_path: Path) -> int:
    """
    Writes a list of dictionaries to a JSONL file.
    Returns the count of written records.
    """
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with open(out_p, "w", encoding="utf-8") as f:
        for item in records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1
    return count
