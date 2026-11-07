"""What the API calls: the examples, a visitor's own file, the limits, the queue and the reports.

- the three examples are checked when the image is built (precompute.py) and read from files at
  start, they cost nothing; without those files (a dev machine) they are checked at start;
- a visitor has CHECKS_PER_DAY checks of their own files a day, then the demo stops politely;
- each check runs in a child process that exits after it (worker.py), WORK_CONCURRENCY at a time
  with at most QUEUE_MAX waiting, so the web process keeps its idle size between checks;
- the model, when one is set, is switched off for the rest of the day after DAILY_TOKEN_BUDGET
  tokens; checks go one at a time, which is also GigaChat's one stream for individuals;
- an uploaded file is not kept: its result and reports live in memory for RESULT_TTL seconds, for
  the downloads, and are dropped after.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import config, contract, invoice, worker
from .company import Company

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


@dataclass
class Stored:
    result: dict
    # fmt -> (bytes or a file with them, download name)
    reports: dict[str, tuple[bytes | Path, str]] = field(default_factory=dict)
    created: float = field(default_factory=time.time)


class Service:
    def __init__(self, company: Company, model_name: str = ""):
        self.company = company
        self.model_name = model_name  # "" when no model is configured
        self.results: dict[str, Stored] = {}
        self.examples: dict[str, dict] = {}
        self._usage: dict[tuple[str, str], int] = {}
        self._tokens: dict[str, int] = {}
        self._lock = threading.Lock()
        self._work = asyncio.Semaphore(config.WORK_CONCURRENCY)
        self._waiting = 0

    # examples ---------------------------------------------------------------------------------

    def load_examples(self) -> None:
        for ex in EXAMPLES:
            stored = self._precomputed(ex["id"]) or self._check_example(ex)
            if stored is None:
                continue
            self.examples[ex["id"]] = stored.result
            self.results[stored.result["id"]] = stored
        log.info("examples ready: %s", ", ".join(self.examples) or "none")

    def _precomputed(self, eid: str) -> Stored | None:
        base = config.PRECOMPUTED_DIR
        path = base / f"{eid}.json"
        if not path.exists():
            return None
        reports = {
            fmt: (base / f"{eid}.{fmt}", (base / f"{eid}.{fmt}.name").read_text(encoding="utf-8"))
            for fmt in ("xlsx", "docx")
        }
        return Stored(json.loads(path.read_text(encoding="utf-8")), reports, created=float("inf"))

    def _check_example(self, ex: dict) -> Stored | None:
        path = config.EXAMPLES_DIR / ex["file"]
        if not path.exists():
            return None
        try:
            out = worker.run(ex["file"], path.read_bytes(), use_model=False)
        except worker.WorkerError as e:  # a scan without Tesseract on a dev machine
            log.warning("example %s: %s", ex["file"], e)
            return None
        result = out["result"]
        result["id"] = f"example-{ex['id']}"
        result["example"] = ex["id"]
        return Stored(result, out["reports"], created=float("inf"))

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
        return bool(self.model_name) and self._tokens.get(date.today().isoformat(), 0) < config.DAILY_TOKEN_BUDGET

    def _spent(self, tokens: int) -> None:
        if tokens:
            day = date.today().isoformat()
            with self._lock:
                self._tokens = {day: self._tokens.get(day, 0) + tokens}

    # checks -----------------------------------------------------------------------------------

    async def check_upload(self, visitor: str, filename: str, data: bytes) -> dict:
        if self.remaining(visitor) <= 0:
            raise LimitError(
                f"На сегодня лимит демо исчерпан: {config.CHECKS_PER_DAY} проверок своих файлов в сутки. "
                "Примеры можно открывать дальше, а свои документы — завтра."
            )
        if len(data) > config.UPLOAD_MAX_BYTES:
            raise CheckError(f"Файл больше {config.UPLOAD_MAX_BYTES // 1_000_000} МБ, пришлите поменьше.")
        if self._waiting >= config.QUEUE_MAX:
            raise BusyError("Сейчас проверяется много документов, повторите через минуту.")
        self._waiting += 1
        try:
            async with self._work:
                out = await asyncio.to_thread(worker.run, filename, data, self._model_on())
        except worker.WorkerError as e:
            raise CheckError(str(e)) from None
        finally:
            self._waiting -= 1
        self._spent(out["tokens"])
        self._count(visitor)
        self._expire()
        result = out["result"]
        result["id"] = uuid.uuid4().hex
        self.results[result["id"]] = Stored(result, out["reports"])
        return result

    def _expire(self) -> None:
        now = time.time()
        for rid, s in list(self.results.items()):
            if now - s.created > config.RESULT_TTL:
                del self.results[rid]
        # a burst of uploads cannot grow memory without bound: the oldest go first
        uploads = sorted((s.created, rid) for rid, s in self.results.items() if s.created != float("inf"))
        for _, rid in uploads[: max(0, len(uploads) - config.RESULTS_MAX)]:
            del self.results[rid]

    # reports ----------------------------------------------------------------------------------

    def get(self, rid: str) -> dict | None:
        self._expire()
        s = self.results.get(rid)
        return s.result if s else None

    def report(self, rid: str, fmt: str) -> tuple[bytes, str] | None:
        self._expire()
        s = self.results.get(rid)
        if s is None or fmt not in s.reports:
            return None
        data, name = s.reports[fmt]
        return (data.read_bytes() if isinstance(data, Path) else data), name

    # what the company checks against, for the reference, rules, suppliers and orders pages -----

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
            "model": self.model_name,
        }
