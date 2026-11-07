"""Wiring for the API: the company, the name of the optional model and the examples."""

from __future__ import annotations

import logging

from . import config, contract
from .company import load
from .service import Service

log = logging.getLogger(__name__)


def model_name() -> str:
    """The configured model, "" without one. The model itself is called only in the check's child."""
    if config.LLM_PROVIDER == "gigachat" and config.GIGACHAT_AUTH_KEY:
        return config.GIGACHAT_MODEL
    if config.LLM_PROVIDER == "openai" and config.OPENAI_API_KEY:
        return config.OPENAI_MODEL
    return ""


def build(model: str | None = None, examples: bool = True) -> Service:
    company = load(config.COMPANY_DIR)
    service = Service(company, model_name() if model is None else model)
    log.info(
        "company %s: %d reference clauses, %d rules, %d suppliers, model %s",
        company.name,
        len(contract.parse(company.reference_text).clauses),
        len(company.rules),
        len(company.suppliers),
        service.model_name or "none",
    )
    if examples:
        service.load_examples()
    return service
