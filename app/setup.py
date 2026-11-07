"""Wiring for the API: the company, the embedding model, the optional LLM and the examples."""

from __future__ import annotations

import logging

from . import config, contract, llm
from .company import load
from .engine.embed import E5Embedder
from .service import Service

log = logging.getLogger(__name__)


def build(embedder=None, model=..., examples: bool = True) -> Service:
    company = load(config.COMPANY_DIR)
    model = llm.from_config() if model is ... else model
    service = Service(company, embedder or E5Embedder(config.MODEL_DIR), model)
    log.info(
        "company %s: %d reference clauses, %d rules, %d suppliers, model %s",
        company.name,
        len(contract.parse(company.reference_text).clauses),
        len(company.rules),
        len(company.suppliers),
        model.name if model else "none",
    )
    if examples:
        service.load_examples()
    return service
