"""Russian company requisites: find them in a text and check their control digits.

ИНН, ОГРН and a bank account all carry a control digit, so a typo or a swapped digit is caught
without any registry. A bank account is checked together with the bank's БИК: the same digits
with a different БИК fail, which is how an invoice with another bank's account shows up.

The examples in this repository use region code 00, which no tax office has, so none of their
numbers can belong to a real company even though every control digit is right.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

INN10_W = (2, 4, 10, 3, 5, 9, 4, 6, 8)
INN12_W1 = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
INN12_W2 = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
ACCOUNT_W = ((7, 1, 3) * 8)[:23]  # 3 digits of the БИК and 20 of the account


def _digits(s: str) -> list[int]:
    return [int(c) for c in s]


def _weighted(digits: list[int], weights) -> int:
    return sum(d * w for d, w in zip(digits, weights, strict=False)) % 11 % 10


def inn_ok(inn: str) -> bool:
    if not inn.isdigit():
        return False
    d = _digits(inn)
    if len(d) == 10:
        return _weighted(d, INN10_W) == d[9]
    if len(d) == 12:
        return _weighted(d, INN12_W1) == d[10] and _weighted(d, INN12_W2) == d[11]
    return False


def ogrn_ok(ogrn: str) -> bool:
    if not ogrn.isdigit() or len(ogrn) not in (13, 15):
        return False
    body, check = int(ogrn[:-1]), int(ogrn[-1])
    return body % (11 if len(ogrn) == 13 else 13) % 10 == check


def kpp_ok(kpp: str) -> bool:
    return bool(re.fullmatch(r"\d{4}[\dA-Z]{2}\d{3}", kpp))


def bik_ok(bik: str) -> bool:
    return bool(re.fullmatch(r"04\d{7}", bik))


def _account_sum(prefix: str, account: str) -> int:
    return sum(int(c) * w % 10 for c, w in zip(prefix + account, ACCOUNT_W, strict=True)) % 10


def account_ok(account: str, bik: str) -> bool:
    """Settlement account (р/с) against the bank's БИК: the last three digits of the БИК go in front."""
    if not (len(account) == 20 and account.isdigit() and bik_ok(bik)):
        return False
    return _account_sum(bik[-3:], account) == 0


def corr_account_ok(account: str, bik: str) -> bool:
    """Correspondent account (к/с): "0" and digits 5–6 of the БИК go in front, and it ends with the БИК's last three."""
    if not (len(account) == 20 and account.isdigit() and bik_ok(bik)) or not account.startswith("301"):
        return False
    return account.endswith(bik[-3:]) and _account_sum("0" + bik[4:6], account) == 0


def with_key(account: str, bik: str, corr: bool = False) -> str:
    """Put the right control digit (the 9th) into an account. For making examples and test data."""
    prefix = "0" + bik[4:6] if corr else bik[-3:]
    for k in "0123456789":
        acc = account[:8] + k + account[9:]
        if _account_sum(prefix, acc) == 0:
            return acc
    raise ValueError(account)


@dataclass
class Requisites:
    inn: str = ""
    kpp: str = ""
    ogrn: str = ""
    bik: str = ""
    account: str = ""  # р/с
    corr_account: str = ""  # к/с
    bank: str = ""

    def as_dict(self) -> dict:
        return asdict(self)

    def problems(self) -> list[str]:
        """What is wrong with the numbers themselves, in words for the report."""
        out = []
        if self.inn and not inn_ok(self.inn):
            out.append(f"ИНН {self.inn}: не сходится контрольная цифра")
        if self.kpp and not kpp_ok(self.kpp):
            out.append(f"КПП {self.kpp}: должен быть из 9 знаков")
        if self.ogrn and not ogrn_ok(self.ogrn):
            out.append(f"ОГРН {self.ogrn}: не сходится контрольная цифра")
        if self.bik and not bik_ok(self.bik):
            out.append(f"БИК {self.bik}: должен быть из 9 цифр и начинаться с 04")
        if self.account and self.bik and bik_ok(self.bik) and not account_ok(self.account, self.bik):
            out.append(f"Р/с {self.account} не сходится с БИК {self.bik}: ошибка в счёте или в банке")
        if self.corr_account and self.bik and bik_ok(self.bik) and not corr_account_ok(self.corr_account, self.bik):
            out.append(f"К/с {self.corr_account} не сходится с БИК {self.bik}")
        return out


@dataclass
class Party:
    role: str = ""  # «Поставщик», «Покупатель», «Получатель»
    name: str = ""
    requisites: Requisites = field(default_factory=Requisites)

    def as_dict(self) -> dict:
        return {"role": self.role, "name": self.name, "requisites": self.requisites.as_dict()}


# Labels as accounting programs print them. Accounts are told apart by their first digits, not by the
# label: the bank block of an invoice labels both the correspondent and the settlement one "Сч. №".
_SP = r"[ \t]*"
_PATTERNS = {
    "inn": rf"ИНН(?:{_SP}/{_SP}КПП)?{_SP}:?{_SP}(\d{{10}}|\d{{12}})\b",
    "kpp": rf"КПП{_SP}:?{_SP}(\d{{9}})\b",
    "ogrn": rf"ОГРН(?:ИП)?{_SP}:?{_SP}(\d{{13}}|\d{{15}})\b",
    "bik": r"БИК[ \t:—–-]*(\d{9})\b",
}
_INN_KPP = re.compile(rf"ИНН{_SP}/{_SP}КПП{_SP}:?{_SP}(\d{{10}}){_SP}/{_SP}(\d{{9}})")
_ACCOUNT = re.compile(r"(?<!\d)(\d{20})(?!\d)")
_BANK = re.compile(r"((?:ПАО|АО|ООО|КБ|АКБ)\s*(?:«[^»\n]{2,60}»|Банк\s+[\wё\- ]{2,40}))", re.IGNORECASE)


def find(text: str) -> Requisites:
    """The first value of each requisite in a piece of text (one party's block)."""
    found = {}
    m = _INN_KPP.search(text)
    if m:
        found["inn"], found["kpp"] = m.group(1), m.group(2)
    for key, pattern in _PATTERNS.items():
        if key in found:
            continue
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            found[key] = m.group(1)
    for acc in _ACCOUNT.findall(text):
        if acc.startswith("30101"):
            found.setdefault("corr_account", acc)
        elif acc.startswith("40"):
            found.setdefault("account", acc)
    bank = ""
    for m in _BANK.finditer(text):
        if "банк" in m.group(1).lower():
            bank = " ".join(m.group(1).split())
            break
    return Requisites(bank=bank, **found)
