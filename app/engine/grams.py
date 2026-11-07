"""How alike two texts are, without a model: character 3- to 5-grams of their words.

A word changes its ending in Russian, its stem keeps most of the n-grams, so «поставщик»,
«поставщика» and «поставщику» stay close, and a reworded clause with the same terms scores high.
Each text becomes a sparse vector of n-gram counts (square-rooted, so a word repeated five times
does not drown the rest) and two texts are compared by cosine. Pure Python on dicts: a contract
against its reference is 25 × 25 small vectors, a few milliseconds and no memory to speak of.
"""

from __future__ import annotations

import math
import re
from collections import Counter

_NON_WORD = re.compile(r"[^\w%]+")


def vector(text: str) -> dict[str, float]:
    t = " " + " ".join(_NON_WORD.sub(" ", text.lower().replace("ё", "е")).split()) + " "
    counts = Counter(t[i : i + n] for n in (3, 4, 5) for i in range(len(t) - n + 1))
    v = {g: math.sqrt(c) for g, c in counts.items()}
    norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
    return {g: x / norm for g, x in v.items()}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(g, 0.0) for g, x in a.items())


def matrix(left: list[str], right: list[str]) -> list[list[float]]:
    lv = [vector(t) for t in left]
    rv = [vector(t) for t in right]
    return [[cosine(a, b) for b in rv] for a in lv]
