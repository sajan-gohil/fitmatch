from __future__ import annotations

import hashlib
import math
from typing import Iterable

from app.core.settings import get_settings


def generate_embedding(text: str, dimensions: int | None = None) -> list[float]:
    settings = get_settings()
    target_dimensions = dimensions or settings.embedding_dimensions
    cleaned = text.strip().lower()
    if not cleaned:
        return [0.0] * target_dimensions

    digest = hashlib.sha256(cleaned.encode("utf-8")).digest()
    vector: list[float] = []
    for index in range(target_dimensions):
        byte = digest[index % len(digest)]
        scaled = (byte / 255.0) * 2 - 1
        vector.append(scaled)
    return vector


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = list(left)
    right_values = list(right)
    if len(left_values) != len(right_values) or not left_values:
        return 0.0

    dot = sum(a * b for a, b in zip(left_values, right_values, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left_values))
    right_norm = math.sqrt(sum(value * value for value in right_values))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    similarity = dot / (left_norm * right_norm)
    return max(-1.0, min(1.0, similarity))
