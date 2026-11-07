from decimal import Decimal

from app import money
from app.requisites import Requisites, account_ok, corr_account_ok, find, inn_ok, ogrn_ok, with_key


def test_control_digits_on_public_bank_numbers():
    # Sberbank's public requisites: the algorithms match the real ones
    assert inn_ok("7707083893")
    assert ogrn_ok("1027700132195")
    assert corr_account_ok("30101810400000000225", "044525225")
    assert not inn_ok("7707083894")
    assert not corr_account_ok("30101810400000000226", "044525225")


def test_twelve_digit_inn():
    assert inn_ok("500100732259")
    assert not inn_ok("500100732250")


def test_account_depends_on_the_bank():
    acc = with_key("40702810000000017384", "040000555")
    assert account_ok(acc, "040000555")
    assert not account_ok(acc, "040000777")  # the same digits in another bank
    typo = acc[:-1] + "5"
    assert not account_ok(typo, "040000555")


def test_problems_in_words():
    r = Requisites(inn="0007318523", bik="040000555", account="40702810000000017385")
    problems = r.problems()
    assert any("ИНН" in p for p in problems)
    assert any("Р/с" in p and "БИК" in p for p in problems)
    assert Requisites(inn="0007318522", bik="040000555", account="40702810000000017384").problems() == []


def test_find_in_an_invoice_bank_block():
    block = (
        "ООО «Банк Образец»\tБИК\t040000555\n"
        "Банк получателя\tСч. №\t30101810300000000555\n"
        "ИНН 0007318522\tКПП 000701001\tСч. №\t40702810000000017384\n"
    )
    r = find(block)
    assert (r.inn, r.kpp, r.bik) == ("0007318522", "000701001", "040000555")
    assert r.corr_account == "30101810300000000555"  # both labelled "Сч. №", told apart by digits
    assert r.account == "40702810000000017384"
    assert r.bank == "ООО «Банк Образец»"


def test_money_parse_and_format():
    assert money.parse("180 540,00") == Decimal("180540.00")
    assert money.parse("49 000-00") == Decimal("49000.00")
    assert money.fmt(Decimal("32556.39")) == "32 556,39"


def test_words_round_trip():
    for x in ("0", "1", "21", "112", "1000", "2001", "31680", "180540", "1000000", "2345678.05"):
        d = Decimal(x)
        assert money.from_words(money.words(d)) == d, money.words(d)
    assert money.words(Decimal("31680")) == "Тридцать одна тысяча шестьсот восемьдесят рублей 00 копеек"
    assert money.words(Decimal("2.01")) == "Два рубля 01 копейка"
