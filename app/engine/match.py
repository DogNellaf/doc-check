"""Pairs between two lists of texts: contract clauses to the reference, invoice lines to the price list.

Every pair gets the score of ai-consultant's search: e5 similarity plus 0.1 of the word overlap
weighted by rarity. Pairs are then taken best first, each text at most once, and a pair counts
only when both numbers pass their thresholds, the same "is it really about the same thing" test
that lets the consultant say "don't know". What is left unpaired is reported: a reference clause
the contract dropped, a clause the supplier added, an invoice line that is not in the price list.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .lexical import idf, overlap, stems

LEXICAL_WEIGHT = 0.1


@dataclass
class Pair:
    left: int
    right: int
    dense: float
    lexical: float

    @property
    def score(self) -> float:
        return self.dense + LEXICAL_WEIGHT * self.lexical


def score_matrix(embedder, left: list[str], right: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Meaning and words for every left × right pair. Both sides are passages: two clauses, two names."""
    if not left or not right:
        shape = (len(left), len(right))
        return np.zeros(shape, dtype=np.float32), np.zeros(shape, dtype=np.float32)
    a = embedder.embed(left, "passage")
    b = embedder.embed(right, "passage")
    dense = a @ b.T
    right_stems = [stems(t) for t in right]
    lex = np.zeros_like(dense)
    for i, text in enumerate(left):
        q = stems(text)
        weights = idf(q, right_stems)
        for j, r in enumerate(right_stems):
            lex[i, j] = overlap(q, r, weights)
    return dense, lex


def align(
    embedder, left: list[str], right: list[str], min_dense: float, min_lexical: float, allowed=None
) -> list[Pair]:
    """Best pairs first, one partner each, both thresholds passed. allowed(i, j) can veto a pair."""
    dense, lex = score_matrix(embedder, left, right)
    cands = [
        Pair(i, j, float(dense[i, j]), float(lex[i, j]))
        for i in range(len(left))
        for j in range(len(right))
        if dense[i, j] >= min_dense and lex[i, j] >= min_lexical and (allowed is None or allowed(i, j))
    ]
    cands.sort(key=lambda p: -p.score)
    used_l, used_r, out = set(), set(), []
    for p in cands:
        if p.left in used_l or p.right in used_r:
            continue
        used_l.add(p.left)
        used_r.add(p.right)
        out.append(p)
    return sorted(out, key=lambda p: p.left)
