"""The buying company: its reference contract, its rules, its suppliers with their price lists, and
its orders. All of it is plain files in COMPANY_DIR that a lawyer or a buyer can edit."""

from __future__ import annotations

import csv
import re
import tomllib
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from .requisites import Requisites


@dataclass
class Rule:
    id: str
    level: str  # high | medium | low
    title: str
    pattern: str
    check: str  # forbid | require | max | min
    why: str
    scope: str = ""
    limit: float | None = None
    fix: str = ""

    def __post_init__(self):
        if self.check not in ("forbid", "require", "max", "min"):
            raise ValueError(f"rule {self.id}: unknown check {self.check!r}")
        if self.check in ("max", "min") and self.limit is None:
            raise ValueError(f"rule {self.id}: {self.check} needs a limit")
        self.rx = re.compile(self.pattern, re.IGNORECASE)
        self.scope_rx = re.compile(self.scope, re.IGNORECASE) if self.scope else None


@dataclass
class PriceItem:
    name: str
    unit: str
    price: Decimal


@dataclass
class OrderLine:
    name: str
    unit: str
    qty: Decimal


@dataclass
class Order:
    number: str  # "З-118"
    date: str
    title: str
    lines: list[OrderLine]


@dataclass
class Supplier:
    name: str
    contract: str
    contract_date: str
    requisites: Requisites
    spec: list[PriceItem] = field(default_factory=list)


@dataclass
class Company:
    name: str
    vat_rate: int
    requisites: Requisites
    reference_text: str
    reference_name: str
    rules: list[Rule]
    suppliers: list[Supplier]
    orders: list[Order]

    def supplier_by_inn(self, inn: str) -> Supplier | None:
        return next((s for s in self.suppliers if s.requisites.inn == inn), None)

    def supplier_by_name(self, text: str) -> Supplier | None:
        key = _name_key(text)
        return next((s for s in self.suppliers if _name_key(s.name) and _name_key(s.name) in key), None)

    def order(self, number: str) -> Order | None:
        key = _number_key(number)
        return next((o for o in self.orders if _number_key(o.number) == key), None)


def _name_key(text: str) -> str:
    m = re.search(r"«([^»]+)»", text)
    return (m.group(1) if m else text).lower().replace("ё", "е").strip()


def _number_key(number: str) -> str:
    # З (Cyrillic) and 3 look the same in a scan; Z is how the file is named
    return re.sub(r"[\s№]", "", number.upper()).replace("З", "Z").replace("3-", "Z-")


def _csv(path: Path) -> tuple[list[dict], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    comment = " ".join(line.lstrip("# ").strip() for line in lines if line.startswith("#"))
    rows = list(csv.DictReader([line for line in lines if not line.startswith("#")], delimiter=";"))
    return rows, comment


def load(path: str | Path) -> Company:
    path = Path(path)
    cfg = tomllib.loads((path / "company.toml").read_text(encoding="utf-8"))
    rules_cfg = tomllib.loads((path / cfg.get("rules", "rules.toml")).read_text(encoding="utf-8"))
    suppliers = []
    for s in cfg.get("supplier", []):
        spec = []
        if s.get("spec"):
            rows, _ = _csv(path / s["spec"])
            spec = [PriceItem(r["name"], r["unit"], Decimal(r["price"])) for r in rows]
        suppliers.append(
            Supplier(s["name"], s["contract"], s["contract_date"], Requisites(**s.get("requisites", {})), spec)
        )
    orders = []
    for f in sorted((path / "orders").glob("*.csv")):
        rows, comment = _csv(f)
        m = re.search(r"№\s*(\S+)\s+от\s+(\d{2}\.\d{2}\.\d{4})", comment)
        orders.append(
            Order(
                m.group(1) if m else f.stem,
                m.group(2) if m else "",
                comment,
                [OrderLine(r["name"], r["unit"], Decimal(r["qty"])) for r in rows],
            )
        )
    ref = cfg.get("reference", "reference-supply.md")
    return Company(
        name=cfg["name"],
        vat_rate=int(cfg.get("vat_rate", 22)),
        requisites=Requisites(**cfg.get("requisites", {})),
        reference_text=(path / ref).read_text(encoding="utf-8"),
        reference_name=ref,
        rules=[Rule(**r) for r in rules_cfg.get("rule", [])],
        suppliers=suppliers,
        orders=orders,
    )
