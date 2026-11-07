from app import contract
from app.contract import Clause, parse, run_rules
from app.reader import read

from .conftest import example


def test_parse_the_supplier_draft():
    doc = parse(read("d.docx", example("dogovor-postavki-31-27.docx")).text)
    assert doc.number == "31/27"
    assert doc.date == ""  # «__» ноября: not filled in
    assert doc.city == "Энск"
    assert len(doc.clauses) == 25
    assert doc.clauses[0].number == "1.1" and doc.clauses[0].section == "Предмет договора"
    roles = {p.role: p for p in doc.parties}
    assert set(roles) == {"Поставщик", "Покупатель"}
    assert roles["Поставщик"].name == "ООО «Зерновая линия»"
    assert roles["Поставщик"].requisites.inn == "0007318522"
    assert roles["Покупатель"].requisites.account == "40702810800000004127"


def test_parse_the_reference(company):
    ref = parse(company.reference_text)
    assert len(ref.clauses) == 25
    assert [c.number for c in ref.clauses[:4]] == ["1.1", "1.2", "1.3", "2.1"]


def test_the_reference_passes_every_rule(company):
    for c in parse(company.reference_text).clauses:
        assert run_rules(company, c) == [], c.number


def _rules(company, text):
    return {f.rule for f in run_rules(company, Clause("1.1", "", text))}


def test_rules_by_numbers(company):
    assert _rules(company, "Покупатель вносит 100 % предоплату каждой партии.") == {"prepayment"}
    assert _rules(company, "Покупатель вносит 30 % предоплату каждой партии.") == set()
    assert _rules(company, "Покупатель уплачивает пени 0,5 % от суммы долга за каждый день просрочки.") == {
        "buyer-penalty",
        "buyer-penalty-cap",
    }
    assert (
        _rules(company, "Покупатель уплачивает неустойку 0,1 % за каждый день просрочки, но не более 10 % от суммы.")
        == set()
    )
    assert _rules(company, "Поставщик уплачивает неустойку 0,05 % за каждый день просрочки поставки.") == {
        "supplier-penalty"
    }


def test_rules_by_wording(company):
    assert "price-unilateral" in _rules(company, "Поставщик вправе в одностороннем порядке повысить цену Товара.")
    assert "jurisdiction" in _rules(company, "Споры рассматриваются в суде по месту нахождения Поставщика.")
    assert "claims-hours" in _rules(company, "Претензии по качеству принимаются в течение 48 часов.")
    assert "pay-to-invoice-account" in _rules(company, "Оплата на расчётный счёт, указанный в счёте Поставщика.")


def test_check_pairs_and_reports(company):
    text = read("d.docx", example("dogovor-postavki-31-27.docx")).text
    r = contract.check(company, text).as_dict()
    assert r["verdict"]["level"] == "high"
    rules = {f["rule"] for f in r["findings"] if f["kind"] == "rule"}
    assert {"prepayment", "price-unilateral", "claims-hours", "jurisdiction"} <= rules
    assert any(f["kind"] == "requisites" for f in r["findings"])
    same = [c for c in r["clauses"] if c["status"] == "same"]
    assert len(same) >= 10


def dated(text):
    """The reference with a date under its title, as a signed contract has."""
    return text.replace("# Договор поставки", "# Договор поставки\n«01» ноября 2026 г.")


def test_the_reference_against_itself(company):
    r = contract.check(company, dated(company.reference_text)).as_dict()
    assert all(c["status"] == "same" for c in r["clauses"])
    assert r["findings"] == []
