"""What a check reports: findings with a level, and the verdict they add up to."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

LEVELS = ("high", "medium", "low")
LEVEL_NAMES = {"high": "Критично", "medium": "Согласовать", "low": "Обратить внимание"}


@dataclass
class Finding:
    level: str  # high | medium | low
    kind: str  # rule | changed | missing | extra | requisites | arithmetic | vat | price | qty | basis | ...
    title: str
    why: str = ""
    where: str = ""  # "п. 3.3", "строка 2", "реквизиты"
    quote: str = ""  # the text of the document it is about
    fix: str = ""  # suggested text: a reference clause or the right number
    ref: str = ""  # reference clause number, "3.3"
    rule: str = ""  # rule id
    anchor: str = ""  # id of the clause or line in the result, for the highlight
    id: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Verdict:
    level: str  # ok | low | medium | high
    text: str
    counts: dict = field(default_factory=dict)


def verdict(findings: list[Finding], kind: str) -> Verdict:
    counts = {lv: sum(1 for f in findings if f.level == lv) for lv in LEVELS}
    texts = {
        "contract": {
            "high": "Не подписывать в этой редакции",
            "medium": "Подписывать после согласования правок",
            "low": "Можно подписывать, есть замечания",
            "ok": "Совпадает с эталоном, можно подписывать",
        },
        "invoice": {
            "high": "Не оплачивать до исправления",
            "medium": "Уточнить у поставщика перед оплатой",
            "low": "Можно оплачивать, есть замечания",
            "ok": "Расхождений нет, можно оплачивать",
        },
    }[kind]
    level = next((lv for lv in LEVELS if counts[lv]), "ok")
    return Verdict(level, texts[level], counts)


def number(findings: list[Finding]) -> list[Finding]:
    order = {lv: i for i, lv in enumerate(LEVELS)}
    findings.sort(key=lambda f: order[f.level])
    for i, f in enumerate(findings, 1):
        f.id = f"f{i}"
    return findings
