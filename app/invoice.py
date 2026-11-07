"""An invoice ("Счёт на оплату"): its lines and totals, checked against the arithmetic, the supplier's
contract, the agreed price list and the order.

The layout is the one 1С and most accounting programs print: the bank block on top, the number and
date, the supplier and the buyer, the basis, a table of lines, the totals with VAT and the total in
words. A scan reads the same way after OCR, with a little tolerance for its spacing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

from . import config
from .company import Company, Order, Supplier
from .engine.match import align
from .findings import Finding, number, verdict
from .money import AMOUNT, fmt, from_words, money, parse
from .requisites import Requisites, find

UNITS = r"шт|кг|г|л|т|м|м2|м3|уп|меш|кор|компл|пач|бут|рул|ящ|пог\.?\s?м|ед|услуга|усл|час|ч"
LINE = re.compile(
    # the row number may be lost or misread in a scan ("a" for "1"), then the line keeps its place
    rf"^\s*(?:(\d{{1,3}})[.)]?\s+|[^\s\d]{{1,2}}\s+)?(.+?)\s+(\d+(?:[.,]\d+)?)\s+({UNITS})\.?\s+({AMOUNT})\s+({AMOUNT})\s*$",
    re.IGNORECASE,
)
SIZE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(кг|г|л|мл|шт|%)(?![а-яё])", re.IGNORECASE)
MONTHS = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()


@dataclass
class Line:
    n: int
    name: str
    qty: Decimal
    unit: str
    price: Decimal
    total: Decimal
    id: str = ""


@dataclass
class Parsed:
    number: str = ""
    date: str = ""
    supplier: str = ""
    buyer: str = ""
    basis: str = ""
    contract: str = ""
    contract_date: str = ""
    order: str = ""
    requisites: Requisites = field(default_factory=Requisites)  # the payee's, from the bank block
    buyer_inn: str = ""
    lines: list[Line] = field(default_factory=list)
    total: Decimal | None = None
    vat_rate: int | None = None
    vat: Decimal | None = None
    to_pay: Decimal | None = None
    count: int | None = None
    words: str = ""


def _amount(pattern: str, text: str) -> Decimal | None:
    m = re.search(pattern + rf"\s*:?\s*({AMOUNT})", text, re.IGNORECASE)
    return parse(m.group(1)) if m else None


def _date(text: str) -> str:
    m = re.search(r"(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(\d{4})", text, re.IGNORECASE)
    if m:
        return f"{int(m.group(1)):02d}.{MONTHS.index(m.group(2).lower()) + 1:02d}.{m.group(3)}"
    m = re.search(r"\d{2}\.\d{2}\.\d{4}", text)
    return m.group(0) if m else ""


def parse_invoice(text: str) -> Parsed:
    p = Parsed()
    flat = re.sub(r"[ \t]+", " ", text)
    m = re.search(r"Сч[её]т\s+(?:на\s+оплату\s+)?№\s*([\w/\-]+)\s+от\s+([^\n]{6,30})", flat, re.IGNORECASE)
    if m:
        p.number, p.date = m.group(1), _date(m.group(2))
    m = re.search(r"(?:Поставщик|Исполнитель)(?:\s*\((?:Исполнитель|Поставщик)\))?\s*:\s*([^\n]+)", flat)
    if m:
        p.supplier = m.group(1).strip(" ,;")
    m = re.search(r"(?:Покупатель|Заказчик)(?:\s*\((?:Заказчик|Покупатель)\))?\s*:\s*([^\n]+)", flat)
    if m:
        p.buyer = m.group(1).strip()
        inn = re.search(r"ИНН\s*(\d{10}|\d{12})", p.buyer)
        p.buyer_inn = inn.group(1) if inn else ""
    m = re.search(r"Основание\s*:\s*([^\n]+)", flat)
    if m:
        p.basis = m.group(1).strip()
        c = re.search(r"[Дд]оговор\w*(?:\s+поставки)?\s*№\s*([\w/\-]+)(?:\s+от\s+(\d{2}\.\d{2}\.\d{4}))?", p.basis)
        if c:
            p.contract, p.contract_date = c.group(1), c.group(2) or ""
        o = re.search(r"[Зз]аказ\w*\s*(?:покупателя\s*)?№\s*([\wЗз]+-?\d+)", p.basis)
        if o:
            p.order = o.group(1)

    # the bank block is above the number of the invoice; the payee's ИНН is there too
    head = flat[: m.start()] if (m := re.search(r"Сч[её]т\s+(?:на\s+оплату\s+)?№", flat, re.IGNORECASE)) else flat
    p.requisites = find(head)
    if not p.requisites.inn and p.supplier:
        p.requisites.inn = find(p.supplier).inn
        p.requisites.kpp = p.requisites.kpp or find(p.supplier).kpp

    for raw in text.splitlines():
        m = LINE.match(re.sub(r"[ \t]+", " ", raw))
        if not m:
            continue
        qty, price, total = parse(m.group(3)), parse(m.group(5)), parse(m.group(6))
        if qty is None or price is None or total is None:
            continue
        name = m.group(2).strip(" ,;")
        n = int(m.group(1)) if m.group(1) else len(p.lines) + 1
        p.lines.append(Line(n, name, qty, m.group(4).lower(), price, total))
    for i, line in enumerate(p.lines, 1):
        line.id = f"l{i}"

    p.total = _amount(r"^\s*Итого(?!\s+НДС)", flat.replace("\n", "\n ")) or _amount(r"\bИтого(?!\s+НДС)", flat)
    m = re.search(r"НДС\s*\(?\s*(\d{1,2})\s*%\s*\)?\s*:?\s*(" + AMOUNT + ")", flat)
    if m:
        p.vat_rate, p.vat = int(m.group(1)), parse(m.group(2))
    elif re.search(r"Без\s+(?:налога\s*\(?)?НДС", flat, re.IGNORECASE):
        p.vat_rate = 0
    p.to_pay = _amount(r"Всего\s+к\s+оплате", flat)
    m = re.search(r"Всего\s+наименований\s+(\d+)", flat)
    if m:
        p.count = int(m.group(1))
    m = re.search(r"\n\s*([А-ЯЁ][а-яё]+(?:\s+[а-яё]+)*\s+рубл[а-яё]*\s+\d{2}\s+копе[а-яё]+)", flat)
    if m:
        p.words = m.group(1).strip()
    return p


# the check ----------------------------------------------------------------------------------------


@dataclass
class InvoiceResult:
    doc: Parsed
    supplier: Supplier | None
    order: Order | None
    findings: list[Finding]
    rows: list[dict]
    lines_by: str = "rules"  # or "model"

    def as_dict(self) -> dict:
        d = self.doc
        v = verdict(self.findings, "invoice")
        return {
            "kind": "invoice",
            "lines_by": self.lines_by,
            "verdict": v.__dict__,
            "fields": [
                {"name": "Документ", "value": f"Счёт на оплату № {d.number}" if d.number else "Счёт на оплату"},
                {"name": "Дата", "value": d.date or "не указана"},
                {"name": "Поставщик", "value": d.supplier or "не найден", "requisites": d.requisites.as_dict()},
                {"name": "Покупатель", "value": d.buyer or "не найден"},
                {"name": "Основание", "value": d.basis or "не указано"},
                {"name": "Договор в карточке", "value": _contract_name(self.supplier) if self.supplier else "нет"},
                {"name": "Заказ", "value": self.order.title if self.order else (d.order or "не указан")},
                {"name": "Итого", "value": fmt(d.total) if d.total is not None else "не найдено"},
                {"name": "НДС", "value": f"{d.vat_rate} %, {fmt(d.vat)}" if d.vat_rate else "без НДС"},
                {"name": "Сумма прописью", "value": d.words or "не найдена"},
            ],
            "findings": [f.as_dict() for f in self.findings],
            "lines": self.rows,
            "totals": {
                "lines": fmt(sum((x.total for x in d.lines), Decimal(0))),
                "total": fmt(d.total),
                "vat": fmt(d.vat),
                "to_pay": fmt(d.to_pay),
            },
        }


def qty(x: Decimal) -> str:
    """20, 2,5: no trailing zeros and no exponent."""
    return f"{x.normalize():f}".replace(".", ",")


def sizes(name: str) -> set[str]:
    """Pack sizes and fat in a name: {"50кг"}, {"82.5%", "20кг"}. The words do not see numbers."""
    return {f"{n.replace(',', '.')}{u.lower()}" for n, u in SIZE.findall(name)}


def same_pack(a: str, b: str) -> bool:
    """ "Мука ржаная, 25 кг" is not "Мука ржаная, 50 кг": both have sizes and they differ."""
    sa, sb = sizes(a), sizes(b)
    return not (sa and sb) or sa == sb


def _match(names: list[str], other: list[str]):
    return align(names, other, config.ITEM_MIN_SIMILARITY, config.ITEM_MIN_LEXICAL,
                 allowed=lambda i, j: same_pack(names[i], other[j]))  # fmt: skip


def _contract_name(s: Supplier) -> str:
    y, mth, day = s.contract_date.split("-")
    return f"№ {s.contract} от {day}.{mth}.{y}"


def _f(level, kind, title, why="", where="", quote="", fix="", anchor="") -> Finding:
    return Finding(level=level, kind=kind, title=title, why=why, where=where, quote=quote, fix=fix, anchor=anchor)


def check(company: Company, text: str, model_lines: list[dict] | None = None) -> InvoiceResult:
    """model_lines: the lines read by the model when the rules found none (see llm.extract_lines)."""
    d = parse_invoice(text)
    lines_by = "rules"
    if not d.lines and model_lines:
        d.lines = [Line(i, x["name"], x["qty"], x["unit"], x["price"], x["total"], f"l{i}")
                   for i, x in enumerate(model_lines, 1)]  # fmt: skip
        lines_by = "model"
    f: list[Finding] = []
    rows = [
        {
            "id": x.id,
            "n": x.n,
            "name": x.name,
            "qty": qty(x.qty),
            "unit": x.unit,
            "price": fmt(x.price),
            "total": fmt(x.total),
            "issues": [],
        }
        for x in d.lines
    ]
    row = {x.id: r for x, r in zip(d.lines, rows, strict=True)}

    def flag(finding: Finding) -> None:
        f.append(finding)
        if finding.anchor in row:
            row[finding.anchor]["issues"].append(finding.level)

    if not d.lines:
        flag(_f("high", "parse", "Не нашлись строки счёта", "Таблица товаров не распознана, проверить суммы "
                "не получится. Пришлите PDF из учётной программы или скан почётче."))  # fmt: skip

    # 1. arithmetic --------------------------------------------------------------------------------
    for x in d.lines:
        expected = money(x.qty * x.price)
        if expected != x.total:
            flag(_f("high", "arithmetic", f"Ошибка в строке {x.n}: сумма не равна цене × количество",
                    f"{qty(x.qty)} × {fmt(x.price)} = {fmt(expected)}, а в счёте {fmt(x.total)}. "
                    f"Разница {fmt(x.total - expected)}.",
                    f"строка {x.n}", x.name, fmt(expected), x.id))  # fmt: skip
    lines_sum = sum((x.total for x in d.lines), Decimal(0))
    if d.lines and d.total is not None and lines_sum != d.total:
        flag(_f("high", "arithmetic", "Итого не равно сумме строк",
                f"Строки дают {fmt(lines_sum)}, в счёте «Итого» {fmt(d.total)}.", "итоги", fix=fmt(lines_sum)))  # fmt: skip
    total = d.total if d.total is not None else lines_sum

    # 2. VAT ---------------------------------------------------------------------------------------
    rate = company.vat_rate
    if d.vat_rate is not None and d.vat_rate not in (0, rate):
        right = money(total * rate / (100 + rate))
        flag(_f("high", "vat", f"НДС {d.vat_rate} % вместо {rate} %",
                f"С 1 января 2026 года ставка НДС — {rate} %. С суммы {fmt(total)} НДС {rate} % составляет "
                f"{fmt(right)}, в счёте {fmt(d.vat)}. Такой счёт-фактуру не примут к вычету.",
                "итоги", fix=fmt(right)))  # fmt: skip
    elif d.vat_rate and d.vat is not None:
        right = money(total * d.vat_rate / (100 + d.vat_rate))
        if abs(right - d.vat) > Decimal("0.01"):
            flag(_f("high", "vat", "Сумма НДС посчитана неверно",
                    f"НДС {d.vat_rate} % в сумме {fmt(total)} — {fmt(right)}, в счёте {fmt(d.vat)}.", "итоги",
                    fix=fmt(right)))  # fmt: skip
    if d.to_pay is not None and d.to_pay != total:
        flag(_f("high", "arithmetic", "«Всего к оплате» не равно «Итого»",
                f"Цены в счёте с НДС, поэтому к оплате должно быть {fmt(total)}, а указано {fmt(d.to_pay)}.",
                "итоги", fix=fmt(total)))  # fmt: skip
    if d.words:
        w = from_words(d.words)
        if w is not None and w != money(d.to_pay or total):
            flag(_f("high", "words", "Сумма прописью не совпадает с цифрами",
                    f"Прописью {fmt(w)}, цифрами {fmt(d.to_pay or total)}. Банк и бухгалтерия ориентируются "
                    "на сумму прописью.", "итоги", d.words))  # fmt: skip
    if d.count is not None and d.lines and d.count != len(d.lines):
        flag(_f("low", "count", "Число наименований не совпадает",
                f"В строке «Всего наименований» {d.count}, в таблице {len(d.lines)}.", "итоги"))  # fmt: skip

    # 3. requisites --------------------------------------------------------------------------------
    for problem in d.requisites.problems():
        flag(_f("high", "requisites", "Ошибка в реквизитах получателя", problem + ".", "реквизиты"))
    supplier = company.supplier_by_inn(d.requisites.inn) or company.supplier_by_name(d.supplier)
    if supplier is None:
        flag(_f("medium", "supplier", "Поставщика нет в карточках компании",
                "С этим поставщиком нет подписанного договора в системе: реквизиты и цены не с чем сверить. "
                "Проверены только суммы и реквизиты.", "поставщик", d.supplier))  # fmt: skip
    else:
        ours, theirs = supplier.requisites, d.requisites
        changed = [
            (label, getattr(ours, key), getattr(theirs, key))
            for key, label in (("inn", "ИНН"), ("kpp", "КПП"), ("bik", "БИК"), ("account", "р/с"))
            if getattr(theirs, key) and getattr(ours, key) and getattr(theirs, key) != getattr(ours, key)
        ]
        if changed:
            what = "; ".join(f"{label} {new} вместо {old}" for label, old, new in changed)
            bank = f" (банк {theirs.bank})" if theirs.bank and theirs.bank != ours.bank else ""
            flag(_f("high", "requisites", "Реквизиты не совпадают с договором",
                    f"{what}{bank}. По договору {_contract_name(supplier)} платим только на счёт из договора, "
                    "о смене реквизитов поставщик сообщает письмом за подписью руководителя. Позвоните "
                    "поставщику по номеру из договора, а не из письма со счётом: так подменяют реквизиты.",
                    "реквизиты", fix=f"р/с {ours.account}, БИК {ours.bik}, {ours.bank}"))  # fmt: skip
        if not d.contract:
            flag(_f("medium", "basis", "В счёте нет ссылки на договор",
                    f"В основании нужно указать договор {_contract_name(supplier)}, иначе оплата не привязана "
                    "к его условиям.", "основание", d.basis))  # fmt: skip
        elif d.contract != supplier.contract:
            flag(_f("medium", "basis", "Счёт ссылается на другой договор",
                    f"В основании договор № {d.contract}, а подписан {_contract_name(supplier)}.", "основание",
                    d.basis))  # fmt: skip
    if company.requisites.inn and d.buyer_inn and d.buyer_inn != company.requisites.inn:
        flag(_f("medium", "buyer", f"Счёт выставлен не на {company.name}",
                f"ИНН покупателя в счёте {d.buyer_inn}, у компании {company.requisites.inn}.", "покупатель",
                d.buyer))  # fmt: skip

    # 4. prices: the supplier's agreed price list ---------------------------------------------------
    if supplier and supplier.spec and d.lines:
        pairs = _match([x.name for x in d.lines], [s.name for s in supplier.spec])
        pair_of = {p.left: p for p in pairs}
        for i, x in enumerate(d.lines):
            p = pair_of.get(i)
            if p is None:
                flag(_f("medium", "price", f"Позиции нет в спецификации: строка {x.n}",
                        f"«{x.name}» не согласована в спецификации к договору {_contract_name(supplier)}, "
                        "цену не с чем сверить.", f"строка {x.n}", x.name, anchor=x.id))  # fmt: skip
                continue
            spec = supplier.spec[p.right]
            rows[i]["spec"] = {"name": spec.name, "price": fmt(spec.price)}
            if x.price > spec.price:
                over = x.price - spec.price
                flag(_f("high", "price", f"Цена выше спецификации: строка {x.n}",
                        f"{fmt(x.price)} вместо {fmt(spec.price)} за {x.unit}: +{fmt(over)}, по строке "
                        f"+{fmt(money(over * x.qty))}. Цена фиксирована договором, менять её можно только "
                        "дополнительным соглашением.", f"строка {x.n}", x.name, fmt(spec.price), x.id))  # fmt: skip
            elif x.price < spec.price:
                flag(_f("low", "price", f"Цена ниже спецификации: строка {x.n}",
                        f"{fmt(x.price)} вместо {fmt(spec.price)}. Проверьте, тот ли это товар.",
                        f"строка {x.n}", x.name, anchor=x.id))  # fmt: skip

    # 5. quantities: the order ----------------------------------------------------------------------
    order = company.order(d.order) if d.order else None
    if d.order and order is None:
        flag(_f("medium", "order", f"Заказа № {d.order} нет в системе", "Количество не с чем сверить.", "основание"))
    if order and d.lines:
        pairs = _match([x.name for x in d.lines], [o.name for o in order.lines])
        pair_of = {p.left: p for p in pairs}
        for i, x in enumerate(d.lines):
            p = pair_of.get(i)
            if p is None:
                flag(_f("medium", "qty", f"Не заказывали: строка {x.n}",
                        f"«{x.name}» нет в заказе № {order.number}. Уберите строку или согласуйте её "
                        "отдельно.", f"строка {x.n}", x.name, anchor=x.id))  # fmt: skip
                continue
            ordered = order.lines[p.right].qty
            rows[i]["ordered"] = qty(ordered)
            if x.qty > ordered:
                flag(_f("medium", "qty", f"Больше, чем в заказе: строка {x.n}",
                        f"В счёте {qty(x.qty)} {x.unit}, заказано {qty(ordered)}. Лишнее — {fmt(money((x.qty - ordered) * x.price))}.",
                        f"строка {x.n}", x.name, str(ordered), x.id))  # fmt: skip
            elif x.qty < ordered:
                flag(_f("low", "qty", f"Меньше, чем в заказе: строка {x.n}",
                        f"В счёте {qty(x.qty)} {x.unit}, заказано {qty(ordered)}. Уточните, когда будет остаток.",
                        f"строка {x.n}", x.name, anchor=x.id))  # fmt: skip
        billed = {p.right for p in pairs}
        for j, o in enumerate(order.lines):
            if j not in billed:
                flag(_f("low", "qty", "Заказанной позиции нет в счёте",
                        f"«{o.name}», {qty(o.qty)} {o.unit} из заказа № {order.number}.", "заказ"))  # fmt: skip

    return InvoiceResult(d, supplier, order, number(f), rows, lines_by)
