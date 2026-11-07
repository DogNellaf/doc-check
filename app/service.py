"""What the API calls: the examples, a visitor's own file, the limits, the queue and the reports.

- the three examples are checked once at start and served from memory, they cost nothing;
- a visitor has CHECKS_PER_DAY checks of their own files a day, then the demo stops politely;
- checks run WORK_CONCURRENCY at a time (OCR and the model take a CPU each), with at most
  QUEUE_MAX waiting, then the visitor is asked to repeat in a minute;
- the model, when one is set, waits in its own queue of LLM_CONCURRENCY and is switched off for
  the rest of the day after DAILY_TOKEN_BUDGET tokens;
- an uploaded file is not kept: its text and report live in memory for RESULT_TTL seconds, for
  the downloads, and are dropped after.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import date

from . import config, contract, invoice, llm, report
from .company import Company
from .reader import ReadError, read

log = logging.getLogger(__name__)

EXAMPLES = [
    {
        "id": "contract",
        "file": "dogovor-postavki-31-27.docx",
        "title": "Договор поставки № 31/27",
        "note": "Проект поставщика на 2027 год, DOCX",
    },
    {
        "id": "invoice",
        "file": "schet-412.pdf",
        "title": "Счёт № 412 на 180 540 ₽",
        "note": "PDF из учётной программы, по заказу З-118",
    },
    {
        "id": "scan",
        "file": "schet-419-skan.pdf",
        "title": "Скан счёта № 419",
        "note": "Картинка без текста, читается распознаванием",
    },
]


class CheckError(ValueError):
    pass


class LimitError(CheckError):
    pass


class BusyError(CheckError):
    pass


def visitor_key(raw: str) -> str:
    """IP salted and hashed: usage rows carry no address."""
    return hashlib.sha256(f"{config.QUOTA_SALT}|{raw}".encode()).hexdigest()[:24]


def detect(text: str) -> str:
    head = text[:2500]
    if re.search(r"сч[её]т\s+(?:на\s+оплату\s+)?№", head, re.IGNORECASE):
        return "invoice"
    clauses = sum(1 for line in text.splitlines() if contract.CLAUSE.match(line))
    if re.search(r"договор", head, re.IGNORECASE) and clauses >= 3:
        return "contract"
    raise CheckError("Это не похоже на договор или счёт на оплату. Пришлите договор с пунктами 1.1, 1.2… или счёт.")


@dataclass
class Stored:
    result: dict
    created: float = field(default_factory=time.time)


class Service:
    def __init__(self, company: Company, embedder, model=None):
        self.company = company
        self.embedder = embedder
        self.model = model
        self.results: dict[str, Stored] = {}
        self.examples: dict[str, dict] = {}
        self._usage: dict[tuple[str, str], int] = {}
        self._tokens: dict[str, int] = {}
        self._lock = threading.Lock()
        self._work = asyncio.Semaphore(config.WORK_CONCURRENCY)
        self._llm = threading.Semaphore(config.LLM_CONCURRENCY)
        self._waiting = 0

    # examples ---------------------------------------------------------------------------------

    def load_examples(self) -> None:
        for ex in EXAMPLES:
            path = config.EXAMPLES_DIR / ex["file"]
            if not path.exists():
                continue
            try:
                result = self.check_bytes(ex["file"], path.read_bytes(), use_model=False)
            except (CheckError, ReadError) as e:  # a scan without Tesseract on a dev machine
                log.warning("example %s: %s", ex["file"], e)
                continue
            result["id"] = f"example-{ex['id']}"
            result["example"] = ex["id"]
            self.examples[ex["id"]] = result
            self.results[result["id"]] = Stored(result, created=float("inf"))
        log.info("examples checked: %s", ", ".join(self.examples) or "none")

    def example_list(self) -> list[dict]:
        out = []
        for ex in EXAMPLES:
            r = self.examples.get(ex["id"])
            out.append({**ex, "ready": r is not None, "verdict": r["verdict"] if r else None,
                        "kind": r["kind"] if r else None})  # fmt: skip
        return out

    # limits -----------------------------------------------------------------------------------

    def remaining(self, visitor: str) -> int:
        return max(0, config.CHECKS_PER_DAY - self._usage.get((date.today().isoformat(), visitor), 0))

    def _count(self, visitor: str) -> None:
        key = (date.today().isoformat(), visitor)
        with self._lock:
            self._usage[key] = self._usage.get(key, 0) + 1
            for k in [k for k in self._usage if k[0] != key[0]]:
                del self._usage[k]

    def _model_on(self) -> bool:
        return self.model is not None and self._tokens.get(date.today().isoformat(), 0) < config.DAILY_TOKEN_BUDGET

    # checks -----------------------------------------------------------------------------------

    def check_bytes(self, filename: str, data: bytes, use_model: bool = True) -> dict:
        doc = read(filename, data)
        kind = detect(doc.text)
        if kind == "contract":
            result = contract.check(self.company, self.embedder, doc.text).as_dict()
        else:
            model_lines = None
            if use_model and self._model_on() and not invoice.parse_invoice(doc.text).lines:
                model_lines = self._model_lines(doc.text)
            result = invoice.check(self.company, self.embedder, doc.text, model_lines).as_dict()
        result.update(file=filename, fmt=doc.fmt, pages=doc.pages, ocr=doc.ocr)
        return result

    def _model_lines(self, text: str) -> list[dict] | None:
        with self._llm:
            try:
                lines, tokens = llm.extract_lines(self.model, text)
            except llm.LLMError as e:
                log.warning("model could not read the lines: %s", e)
                return None
        day = date.today().isoformat()
        with self._lock:
            self._tokens = {day: self._tokens.get(day, 0) + tokens}
        return lines

    async def check_upload(self, visitor: str, filename: str, data: bytes) -> dict:
        if self.remaining(visitor) <= 0:
            raise LimitError(
                f"На сегодня лимит демо исчерпан: {config.CHECKS_PER_DAY} проверок своих файлов в сутки. "
                "Примеры можно открывать дальше, а свои документы — завтра."
            )
        if self._waiting >= config.QUEUE_MAX:
            raise BusyError("Сейчас проверяется много документов, повторите через минуту.")
        self._waiting += 1
        try:
            async with self._work:
                result = await asyncio.to_thread(self.check_bytes, filename, data)
        finally:
            self._waiting -= 1
        self._count(visitor)
        self._expire()
        result["id"] = uuid.uuid4().hex
        self.results[result["id"]] = Stored(result)
        return result

    def _expire(self) -> None:
        now = time.time()
        for rid, s in list(self.results.items()):
            if now - s.created > config.RESULT_TTL:
                del self.results[rid]

    # reports ----------------------------------------------------------------------------------

    def get(self, rid: str) -> dict | None:
        self._expire()
        s = self.results.get(rid)
        return s.result if s else None

    def report(self, rid: str, fmt: str) -> tuple[bytes, str] | None:
        result = self.get(rid)
        if result is None:
            return None
        stem = re.sub(r"\.[a-z]+$", "", result.get("file", "document"), flags=re.IGNORECASE)
        if fmt == "xlsx":
            return report.xlsx(result), f"{stem}-проверка.xlsx"
        if result["kind"] == "contract":
            return report.contract_docx(result), f"{stem}-правки.docx"
        return report.invoice_docx(result, self.company.name), f"{stem}-письмо.docx"

    # what the company checks against, for the "Эталон и правила" tab -----------------------------

    def company_info(self) -> dict:
        co = self.company
        ref = contract.parse(co.reference_text)
        return {
            "name": co.name,
            "requisites": co.requisites.as_dict(),
            "vat_rate": co.vat_rate,
            "reference_name": co.reference_name,
            "reference": [{"number": c.number, "section": c.section, "text": c.text} for c in ref.clauses],
            "rules": [
                {"id": r.id, "level": r.level, "title": r.title, "why": r.why, "check": r.check, "limit": r.limit}
                for r in co.rules
            ],
            "suppliers": [
                {
                    "name": s.name,
                    "contract": f"№ {s.contract} от {'.'.join(reversed(s.contract_date.split('-')))}",
                    "requisites": s.requisites.as_dict(),
                    "spec": [{"name": i.name, "unit": i.unit, "price": str(i.price)} for i in s.spec],
                }
                for s in co.suppliers
            ],
            "orders": [
                {
                    "number": o.number,
                    "date": o.date,
                    "title": o.title,
                    "lines": [{"name": x.name, "unit": x.unit, "qty": invoice.qty(x.qty)} for x in o.lines],
                }
                for o in co.orders
            ],  # fmt: skip
            "model": self.model.name if self.model else "",
        }
