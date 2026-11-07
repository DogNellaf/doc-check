"""Settings from the environment (.env next to docker-compose.yml). Every one has a default that
runs the demo company without keys: no model, every check is made by the rules and the search."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _list(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


COMPANY_DIR = Path(os.getenv("COMPANY_DIR", str(ROOT / "knowledge" / "kolosok")))
EXAMPLES_DIR = Path(os.getenv("EXAMPLES_DIR", str(ROOT / "examples")))
# Clause and line matching: a pair counts when both numbers pass, as the consultant's "don't know".
# Similarity is by character n-grams; a clause with the reference's number gets a bonus on top.
CLAUSE_MIN_SIMILARITY = _float("CLAUSE_MIN_SIMILARITY", 0.5)
CLAUSE_NUMBER_BONUS = _float("CLAUSE_NUMBER_BONUS", 0.25)
CLAUSE_MIN_LEXICAL = _float("CLAUSE_MIN_LEXICAL", 0.25)
ITEM_MIN_SIMILARITY = _float("ITEM_MIN_SIMILARITY", 0.6)
ITEM_MIN_LEXICAL = _float("ITEM_MIN_LEXICAL", 0.75)

# Model: "none" (default) runs on the rules and the search alone. "gigachat" or "openai" (any
# OpenAI-compatible API) also read the fields of a document the rules could not parse.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower()
GIGACHAT_AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY", "")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat-2")
# GigaChat's certificates chain to the Russian Trusted Root CA, which is not in the usual bundles:
# the repository carries it in certs/
_CA = ROOT / "certs" / "russian_trusted_ca.pem"
GIGACHAT_CA_BUNDLE = os.getenv("GIGACHAT_CA_BUNDLE", str(_CA) if _CA.exists() else "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
LLM_TIMEOUT = _float("LLM_TIMEOUT", 60)

# Limits. Examples are checked when the image is built and cost nothing; a visitor's file takes one.
CHECKS_PER_DAY = _int("CHECKS_PER_DAY", 10)
DAILY_TOKEN_BUDGET = _int("DAILY_TOKEN_BUDGET", 200_000)
WORK_CONCURRENCY = _int("WORK_CONCURRENCY", 1)  # checks at once: OCR and the model take a CPU each
QUEUE_MAX = _int("QUEUE_MAX", 20)
QUOTA_SALT = os.getenv("QUOTA_SALT", "change-me")

# Uploads: kept in memory with their report for RESULT_TTL seconds, then dropped.
UPLOAD_MAX_BYTES = _int("UPLOAD_MAX_BYTES", 5_000_000)
MAX_PAGES = _int("MAX_PAGES", 15)
MAX_CHARS = _int("MAX_CHARS", 60_000)
RESULT_TTL = _int("RESULT_TTL", 3600)
OCR_LANG = os.getenv("OCR_LANG", "rus+eng")
OCR_TIMEOUT = _int("OCR_TIMEOUT", 40)
OCR_MAX_PAGES = _int("OCR_MAX_PAGES", 5)  # scanned pages in one PDF: about 5 s and 100 MB each
# A check runs in a child process (worker.py); after this many seconds it is stopped. Keep it under
# the proxy's read timeout (90 s on the site).
CHECK_TIMEOUT = _int("CHECK_TIMEOUT", 80)
RESULTS_MAX = _int("RESULTS_MAX", 200)  # uploads kept for downloads at once, the oldest go first
PRECOMPUTED_DIR = Path(os.getenv("PRECOMPUTED_DIR", str(ROOT / "precomputed")))

ALLOWED_ORIGINS = _list("ALLOWED_ORIGINS", "*")
