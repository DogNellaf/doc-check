"""Acceptance with the real thresholds: every planted problem of the three examples is
found, and a clean contract and a clean invoice get no findings at all."""

import pytest

from app import contract, invoice
from app.reader import read

from .conftest import HAS_TESSERACT, example

CONTRACT = {
    ("rule", "price-unilateral", "п. 3.2"),
    ("rule", "prepayment", "п. 3.3"),
    ("rule", "pay-to-invoice-account", "п. 3.4"),
    ("rule", "claims-hours", "п. 4.3"),
    ("rule", "buyer-penalty", "п. 5.2"),
    ("rule", "buyer-penalty-cap", "п. 5.2"),
    ("rule", "delivery-paid-by-buyer", "п. 2.2"),
    ("rule", "supplier-penalty", "п. 5.1"),
    ("rule", "liability-exclusion", "п. 5.4"),
    ("rule", "jurisdiction", "п. 7.2"),
    ("rule", "termination-notice", "п. 8.2"),
    ("rule", "termination-debt", "п. 8.2"),
    ("rule", "auto-renewal", "п. 8.1"),
    ("missing", "", "после п. 4.3"),
    ("requisites", "", "реквизиты"),
    ("changed", "", "п. 2.1"),
    ("changed", "", "п. 4.1"),
    ("field", "", "шапка"),
}
INVOICE = {
    ("arithmetic", "строка 5"),
    ("requisites", "реквизиты"),
    ("price", "строка 2"),
    ("qty", "строка 3"),
    ("price", "строка 7"),
    ("qty", "строка 7"),
}


def test_contract_example(company):
    r = contract.check(company, read("d.docx", example("dogovor-postavki-31-27.docx")).text).as_dict()
    got = {(f["kind"], f["rule"], f["where"]) for f in r["findings"]}
    assert got == CONTRACT
    pairs = {c["number"]: c["ref"] for c in r["clauses"]}
    assert all(pairs[n] == n for n in pairs if n != "5.4")  # every clause meets its reference
    assert pairs["5.4"] == ""
    fixes = {f["rule"]: f["fix"] for f in r["findings"] if f["kind"] == "rule"}
    assert fixes["prepayment"].startswith("Покупатель оплачивает каждую партию Товара в течение 14")


def test_invoice_example(company):
    r = invoice.check(company, read("s.pdf", example("schet-412.pdf")).text).as_dict()
    assert {(f["kind"], f["where"]) for f in r["findings"]} == INVOICE
    assert [x.get("spec", {}).get("price") for x in r["lines"]][:6] == [
        "2 450,00", "1 980,00", "18 600,00", "3 900,00", "2 100,00", "4 680,00",
    ]  # fmt: skip


@pytest.mark.skipif(not HAS_TESSERACT, reason="no tesseract")
def test_scan_example(company):
    r = invoice.check(company, read("s.pdf", example("schet-419-skan.pdf")).text).as_dict()
    assert [(f["kind"], f["title"]) for f in r["findings"]] == [("vat", "НДС 20 % вместо 22 %")]


def test_no_false_alarms(company):
    r = contract.check(
        company, company.reference_text.replace("# Договор поставки", "# Договор поставки\n«01» ноября 2026 г.")
    ).as_dict()
    assert r["findings"] == [] and r["verdict"]["level"] == "ok"

    from scripts.make_examples import INVOICE_412, make_invoice_pdf

    clean = {**INVOICE_412, "bank": "ООО «Банк Образец»", "bik": "040000555", "corr": "30101810300000000555",
             "account": "40702810000000017384"}  # fmt: skip
    clean["lines"] = [
        ("Мука пшеничная хлебопекарная в/с, мешок 50 кг", 20, "меш", "2450.00", None),
        ("Мука ржаная обдирная, мешок 50 кг", 6, "меш", "1980.00", None),
        ("Масло сливочное 82,5 %, монолит 20 кг", 3, "кор", "18600.00", None),
        ("Сахар белый, мешок 50 кг", 4, "меш", "3900.00", None),
        ("Дрожжи прессованные, коробка 10 кг", 2, "кор", "2100.00", None),
        ("Яйцо куриное С0, коробка 360 шт", 5, "кор", "4680.00", None),
    ]
    r = invoice.check(company, read("c.pdf", make_invoice_pdf(clean)).text).as_dict()
    assert r["findings"] == [] and r["verdict"]["level"] == "ok"
