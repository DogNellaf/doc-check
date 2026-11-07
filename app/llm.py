"""Model providers behind one interface, the same as in ai-consultant: the checker only calls
complete(), switching GigaChat for an OpenAI-compatible API is a change in .env.

The model is optional and does one job: when the rules cannot find the lines of an invoice (an
unusual layout, a bad scan), it reads them out as JSON. Every check after that is still made by
the code, so a model mistake shows up as a mismatch, not as a wrong "all good".

Mind the licence of the key: the GigaChat freemium for individuals is for personal
non-commercial use only. A company's checker needs a paid package or a company contract.
"""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

import httpx

from . import config

LINES_PROMPT = (
    "Ты читаешь текст счёта на оплату. Выпиши строки таблицы товаров как JSON-массив объектов с полями "
    "name (наименование), qty (количество, число), unit (единица), price (цена, число), total (сумма, число). "
    "Числа пиши с точкой, без пробелов. Бери только то, что есть в тексте, ничего не исправляй и не считай. "
    "Ответь только JSON-массивом, без пояснений."
)


@dataclass
class Completion:
    text: str
    tokens: int


class LLM(Protocol):
    name: str

    def complete(self, system: str, messages: list[dict]) -> Completion: ...


class LLMError(RuntimeError):
    pass


class GigaChat:
    """GigaChat REST API: an OAuth token for 30 minutes, then OpenAI-like chat/completions."""

    name = "gigachat"
    OAUTH = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    CHAT = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    def __init__(self, auth_key: str, scope: str, model: str, ca_bundle: str = "", timeout: float = 60):
        if not auth_key:
            raise LLMError("GIGACHAT_AUTH_KEY is empty")
        self.auth_key, self.scope, self.model = auth_key, scope, model
        self.http = httpx.Client(verify=ca_bundle or True, timeout=timeout)
        self._token, self._expires = "", 0.0

    def _access_token(self) -> str:
        if self._token and time.time() < self._expires - 60:
            return self._token
        r = self.http.post(
            self.OAUTH,
            headers={"Authorization": f"Basic {self.auth_key}", "RqUID": str(uuid.uuid4())},
            data={"scope": self.scope},
        )
        if r.status_code != 200:
            raise LLMError(f"GigaChat OAuth {r.status_code}: {r.text[:200]}")
        data = r.json()
        self._token, self._expires = data["access_token"], data["expires_at"] / 1000
        return self._token

    def complete(self, system: str, messages: list[dict]) -> Completion:
        body = {"model": self.model, "messages": [{"role": "system", "content": system}, *messages], "temperature": 0}
        r = self.http.post(self.CHAT, headers={"Authorization": f"Bearer {self._access_token()}"}, json=body)
        if r.status_code != 200:
            raise LLMError(f"GigaChat {r.status_code}: {r.text[:200]}")
        data = r.json()
        return Completion(
            data["choices"][0]["message"]["content"].strip(), data.get("usage", {}).get("total_tokens", 0)
        )


class OpenAICompatible:
    name = "openai"

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 60):
        if not model:
            raise LLMError("OPENAI_MODEL is empty")
        self.model = model
        self.http = httpx.Client(
            base_url=base_url.rstrip("/"), timeout=timeout, headers={"Authorization": f"Bearer {api_key}"}
        )

    def complete(self, system: str, messages: list[dict]) -> Completion:
        body = {"model": self.model, "messages": [{"role": "system", "content": system}, *messages], "temperature": 0}
        r = self.http.post("/chat/completions", json=body)
        if r.status_code != 200:
            raise LLMError(f"{self.model} {r.status_code}: {r.text[:200]}")
        data = r.json()
        return Completion(
            data["choices"][0]["message"]["content"].strip(), data.get("usage", {}).get("total_tokens", 0)
        )


def from_config() -> LLM | None:
    if config.LLM_PROVIDER == "gigachat":
        return GigaChat(
            config.GIGACHAT_AUTH_KEY,
            config.GIGACHAT_SCOPE,
            config.GIGACHAT_MODEL,
            config.GIGACHAT_CA_BUNDLE,
            config.LLM_TIMEOUT,
        )
    if config.LLM_PROVIDER == "openai":
        return OpenAICompatible(config.OPENAI_BASE_URL, config.OPENAI_API_KEY, config.OPENAI_MODEL, config.LLM_TIMEOUT)
    if config.LLM_PROVIDER in ("", "none"):
        return None
    raise LLMError(f"unknown LLM_PROVIDER {config.LLM_PROVIDER!r}")


def extract_lines(model: LLM, text: str) -> tuple[list[dict], int]:
    """Invoice lines read by the model: [{name, qty, unit, price, total}] with Decimals, and the tokens spent."""
    done = model.complete(LINES_PROMPT, [{"role": "user", "content": text[:12_000]}])
    m = re.search(r"\[.*\]", done.text, re.S)
    if not m:
        raise LLMError("the model did not return a JSON array")
    try:
        raw = json.loads(m.group(0))
        lines = [
            {
                "name": str(x["name"]).strip(),
                "qty": Decimal(str(x["qty"])),
                "unit": str(x.get("unit", "")).strip(),
                "price": Decimal(str(x["price"])).quantize(Decimal("0.01")),
                "total": Decimal(str(x["total"])).quantize(Decimal("0.01")),
            }
            for x in raw
        ]
    except (ValueError, KeyError, TypeError, ArithmeticError) as e:
        raise LLMError(f"bad lines from the model: {e}") from e
    return lines, done.tokens
