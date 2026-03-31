from __future__ import annotations

from pathlib import Path


def parse_resume(file_name: str) -> dict[str, object]:
    suffix = Path(file_name).suffix.lower()
    inferred_role = "Software Engineer"

    if "data" in file_name.lower():
        inferred_role = "Data Analyst"

    return {
        "source_file": file_name,
        "format": suffix.lstrip("."),
        "summary": "Parsed placeholder output. Replace with LLM integration in a later phase.",
        "skills": ["python", "sql"],
        "target_role": inferred_role,
    }
