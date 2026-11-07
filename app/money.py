"""Amounts the way Russian documents write them: "1 234 567,89", "49 000-00", and in words.

An invoice carries the total twice, in digits and in words ("Сто восемьдесят тысяч пятьсот сорок
рублей 00 копеек"), so the words are read back into a number and compared.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
AMOUNT = r"\d{1,3}(?:[   ]\d{3})+(?:[,.]\d{2})?|\d+(?:[,.]\d{2})?"


def parse(text: str) -> Decimal | None:
    s = re.sub(r"[\s  ]", "", text).replace(",", ".")
    s = re.sub(r"-(\d{2})$", r".\1", s)
    try:
        return Decimal(s).quantize(CENT)
    except ArithmeticError:
        return None


def fmt(x: Decimal | int | float | None) -> str:
    """1 234 567,89 with a thin space for thousands, as in the documents."""
    if x is None:
        return "—"
    x = Decimal(x).quantize(CENT, ROUND_HALF_UP)
    whole, frac = f"{x:.2f}".split(".")
    sign = "-" if whole.startswith("-") else ""
    whole = whole.lstrip("-")
    groups = []
    while whole:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    return f"{sign}{' '.join(groups)},{frac}"


def money(x: Decimal) -> Decimal:
    return Decimal(x).quantize(CENT, ROUND_HALF_UP)


# words -> number ---------------------------------------------------------------------------------

_UNITS = {
    "ноль": 0, "один": 1, "одна": 1, "одно": 1, "два": 2, "две": 2, "три": 3, "четыре": 4, "пять": 5,
    "шесть": 6, "семь": 7, "восемь": 8, "девять": 9, "десять": 10, "одиннадцать": 11, "двенадцать": 12,
    "тринадцать": 13, "четырнадцать": 14, "пятнадцать": 15, "шестнадцать": 16, "семнадцать": 17,
    "восемнадцать": 18, "девятнадцать": 19, "двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50,
    "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80, "девяносто": 90, "сто": 100, "двести": 200,
    "триста": 300, "четыреста": 400, "пятьсот": 500, "шестьсот": 600, "семьсот": 700, "восемьсот": 800,
    "девятьсот": 900,
}  # fmt: skip
_SCALES = {"тысяч": 1000, "миллион": 1_000_000, "миллиард": 1_000_000_000}

_UNITS_M = ["", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
_UNITS_F = ["", "одна", "две"] + _UNITS_M[3:]
_TEENS = [
    "десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать", "пятнадцать", "шестнадцать",
    "семнадцать", "восемнадцать", "девятнадцать",
]  # fmt: skip
_TENS = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят", "семьдесят", "восемьдесят", "девяносто"]
_HUNDREDS = ["", "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот", "семьсот", "восемьсот", "девятьсот"]


def plural(n: int, one: str, few: str, many: str) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def _triple(n: int, feminine: bool) -> list[str]:
    out = [_HUNDREDS[n // 100]]
    rest = n % 100
    if 10 <= rest < 20:
        out.append(_TEENS[rest - 10])
    else:
        out += [_TENS[rest // 10], (_UNITS_F if feminine else _UNITS_M)[rest % 10]]
    return [w for w in out if w]


def words(x: Decimal) -> str:
    """180540.00 -> "Сто восемьдесят тысяч пятьсот сорок рублей 00 копеек"."""
    x = money(x)
    rub, kop = int(x), int((x - int(x)) * 100)
    parts: list[str] = []
    scales = [(1_000_000_000, ("миллиард", "миллиарда", "миллиардов"), False),
              (1_000_000, ("миллион", "миллиона", "миллионов"), False),
              (1000, ("тысяча", "тысячи", "тысяч"), True)]  # fmt: skip
    n = rub
    for size, forms, fem in scales:
        if n >= size:
            k, n = divmod(n, size)
            parts += _triple(k, fem) + [plural(k, *forms)]
    parts += _triple(n, False)
    text = " ".join(parts) or "ноль"
    return f"{text[0].upper()}{text[1:]} {plural(rub, 'рубль', 'рубля', 'рублей')} {kop:02d} {plural(kop, 'копейка', 'копейки', 'копеек')}"


def from_words(text: str) -> Decimal | None:
    """The rubles and kopecks of an amount in words, or None when the text has no number words."""
    t = text.lower().replace("ё", "е")
    m = re.search(r"руб\w*\s*(\d{1,2})\s*коп", t)
    kop = int(m.group(1)) if m else 0
    total, current, seen = 0, 0, False
    for w in re.findall(r"[а-я]+", t.split("руб")[0]):
        if w in _UNITS:
            current += _UNITS[w]
            seen = True
            continue
        for stem, size in _SCALES.items():
            if w.startswith(stem):
                total += max(current, 1) * size
                current, seen = 0, True
                break
    if not seen:
        return None
    return Decimal(total + current) + Decimal(kop) / 100
