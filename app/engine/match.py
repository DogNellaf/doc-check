"""Pairs between two lists of texts: contract clauses to the reference, invoice lines to the price list.

Every pair gets two numbers: how alike the texts are by character n-grams (grams.py) and the word
overlap weighted by rarity (lexical.py, ai-consultant's search). A caller may add a bonus to a pair,
the contract adds one when the clause numbers match: a lawyer reads clause 3.2 against 3.2 first.
Pairs are then taken best first, each text at most once, and a pair counts only when both numbers
pass their thresholds. What is left unpaired is reported: a reference clause the contract dropped,
a clause the supplier added, an invoice line that is not in the price list.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from . import grams
from .lexical import idf, overlap, stems

LEXICAL_WEIGHT = 0.1


@dataclass
class Pair:
    left: int
    right: int
    similarity: float  # n-grams plus the caller's bonus
    lexical: float

    @property
    def score(self) -> float:
        return self.similarity + LEXICAL_WEIGHT * self.lexical


def score_matrix(left: list[str], right: list[str]) -> tuple[list[list[float]], list[list[float]]]:
    """N-gram similarity and word overlap for every left × right pair."""
    sim = grams.matrix(left, right)
    right_stems = [stems(t) for t in right]
    lex = []
    for text in left:
        q = stems(text)
        weights = idf(q, right_stems)
        lex.append([overlap(q, r, weights) for r in right_stems])
    return sim, lex


def align(
    left: list[str],
    right: list[str],
    min_similarity: float,
    min_lexical: float,
    bonus: Callable[[int, int], float] | None = None,
    allowed: Callable[[int, int], bool] | None = None,
) -> list[Pair]:
    """Best pairs first, one partner each, both thresholds passed. allowed(i, j) can veto a pair."""
    if not left or not right:
        return []
    sim, lex = score_matrix(left, right)
    cands = []
    for i in range(len(left)):
        for j in range(len(right)):
            s = sim[i][j] + (bonus(i, j) if bonus else 0.0)
            if s >= min_similarity and lex[i][j] >= min_lexical and (allowed is None or allowed(i, j)):
                cands.append(Pair(i, j, s, lex[i][j]))
    cands.sort(key=lambda p: -p.score)
    used_l, used_r, out = set(), set(), []
    for p in cands:
        if p.left in used_l or p.right in used_r:
            continue
        used_l.add(p.left)
        used_r.add(p.right)
        out.append(p)
    return sorted(out, key=lambda p: p.left)
