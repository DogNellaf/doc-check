from decimal import Decimal

import pytest

from app import invoice
from app.invoice import parse_invoice, same_pack
from app.reader import read

from .conftest import HAS_TESSERACT, example


@pytest.fixture(scope="module")
def text_412():
    return read("s.pdf", example("schet-412.pdf")).text


def test_parse_the_invoice(text_412):
    p = parse_invoice(text_412)
    assert (p.number, p.date) == ("412", "05.11.2026")
    assert (p.contract, p.contract_date, p.order) == ("14/26", "01.09.2026", "З-118")
    assert len(p.lines) == 7
    assert p.lines[4].name == "Дрожжи прессованные, коробка 10 кг"
    assert (p.lines[4].qty, p.lines[4].price, p.lines[4].total) == (Decimal(2), Decimal("2100.00"), Decimal("4400.00"))
    assert p.total == Decimal("180540.00") and p.vat_rate == 22 and p.vat == Decimal("32556.39")
    assert p.requisites.bik == "040000777" and p.requisites.account == "40702810200000092615"
    assert p.words.startswith("Сто восемьдесят тысяч")
    assert p.buyer_inn == "0004127368"


def test_pack_sizes():
    assert same_pack("Мука ржаная, мешок 50 кг", "Мука ржаная обдирная, мешок 50 кг")
    assert not same_pack("Мука ржаная, мешок 25 кг", "Мука ржаная обдирная, мешок 50 кг")
    assert not same_pack("Масло сливочное 72,5 %, 20 кг", "Масло сливочное 82,5 %, монолит 20 кг")
    assert same_pack("Услуги доставки", "Мука, 50 кг")  # nothing to compare


def test_arithmetic_vat_words_and_requisites(company, text_412):
    r = invoice.check(company, text_412).as_dict()
    kinds = [(f["kind"], f["where"]) for f in r["findings"]]
    assert ("arithmetic", "строка 5") in kinds
    assert ("requisites", "реквизиты") in kinds
    assert not any(k == "vat" for k, _ in kinds)
    assert not any(k == "words" for k, _ in kinds)


def test_vat_rate_and_words_mismatch(company):
    text = (
        "Счёт на оплату № 7 от 1 ноября 2026 г.\nПоставщик: ООО «Где-то», ИНН 0007318522\n"
        "1 Соль поваренная пищевая, мешок 25 кг 4 меш 520,00 2 080,00\n"
        "Итого: 2 080,00\nВ том числе НДС (20%): 346,67\nВсего к оплате: 2 080,00\n"
        "Две тысячи девяносто рублей 00 копеек\n"
    )
    r = invoice.check(company, text).as_dict()
    titles = {f["kind"]: f for f in r["findings"]}
    assert titles["vat"]["title"] == "НДС 20 % вместо 22 %"
    assert titles["vat"]["fix"] == "375,08"
    assert titles["words"]["level"] == "high"
    assert titles["basis"]["level"] == "medium"  # no contract in the basis


def test_unknown_supplier(company):
    text = (
        "ООО «Банк Пример»\tБИК 040000321\nИНН 0004127368\tСч. № 40702810800000004127\n"
        "Счёт на оплату № 1 от 02.11.2026\nПоставщик: ООО «Чужой поставщик», ИНН 0004127368\n"
        "1 Ремонт тестомеса 1 усл 5 000,00 5 000,00\nИтого: 5 000,00\nБез налога (НДС)\n"
    )
    r = invoice.check(company, text).as_dict()
    assert [f["kind"] for f in r["findings"]] == ["supplier"]
    assert r["verdict"]["level"] == "medium"


def test_lines_from_the_model(company):
    text = "Счёт на оплату № 9 от 03.11.2026\nПоставщик: ООО «Зерновая линия», ИНН 0007318522\nИтого: 520,00\n"
    lines = [{"name": "Соль поваренная пищевая, мешок 25 кг", "qty": Decimal(1), "unit": "меш",
              "price": Decimal("520.00"), "total": Decimal("520.00")}]  # fmt: skip
    r = invoice.check(company, text, lines).as_dict()
    assert r["lines_by"] == "model"
    assert len(r["lines"]) == 1
    assert not any(f["kind"] == "parse" for f in r["findings"])


@pytest.mark.skipif(not HAS_TESSERACT, reason="no tesseract")
def test_the_scan_reads_by_ocr():
    t = read("s.pdf", example("schet-419-skan.pdf"))
    assert t.ocr
    p = parse_invoice(t.text)
    assert len(p.lines) == 4
    assert p.total == Decimal("31680.00") and p.vat_rate == 20
    assert p.requisites.account == "40702810000000017384"
