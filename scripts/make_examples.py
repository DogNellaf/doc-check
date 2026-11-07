"""Make the three example documents in examples/: a supplier's draft contract (DOCX), an invoice
(PDF from an accounting program) and a scanned invoice (a PDF of one picture, read by OCR).

The companies, people and requisites are made up. The requisites carry region code 00, which
no tax office has, so no number here can belong to a real company; the control digits are right,
except where an example is meant to show a mistake.

    python scripts/make_examples.py      # needs reportlab from requirements-dev.txt
"""

from __future__ import annotations

import io
import random
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.money import fmt, words  # noqa: E402

OUT = ROOT / "examples"
FONTS = Path(__file__).resolve().parent / "fonts"

SUPPLIER = {
    "name": "ООО «Зерновая линия»",
    "full": "Общество с ограниченной ответственностью «Зерновая линия»",
    "address": "г. Энск, Промышленный проезд, 4, склад 2",
    "inn": "0007318522",
    "kpp": "000701001",
    "ogrn": "1210000073183",
    "bank": "ООО «Банк Образец»",
    "bik": "040000555",
    "corr": "30101810300000000555",
    "account": "40702810000000017384",
    "head": "Соколов И. П.",
    "accountant": "Рябова Е. В.",
}
BUYER = {
    "name": "ООО «Колосок»",
    "address": "г. Энск, ул. Садовая, 12",
    "inn": "0004127368",
    "kpp": "000401001",
    "ogrn": "1200000041273",
    "bank": "АО «Банк Пример»",
    "bik": "040000321",
    "corr": "30101810000000000321",
    "account": "40702810800000004127",
    "head": "Белова М. А.",
}

# The supplier's draft for 2027: the reference contract with the terms moved in the supplier's favour.
DRAFT = [
    ("1. ПРЕДМЕТ ДОГОВОРА", [
        "1.1. Поставщик обязуется передавать в собственность Покупателя продукты и сырьё для хлебопекарного "
        "производства (далее — Товар), а Покупатель обязуется принимать и оплачивать Товар.",
        "1.2. Наименование, количество, цена и сроки поставки каждой партии согласуются в заказе Покупателя на "
        "основании Спецификации (Приложение № 1).",
        "1.3. Поставщик гарантирует, что Товар принадлежит ему на праве собственности, не заложен и не находится "
        "под арестом.",
    ]),
    ("2. ПОРЯДОК ПОСТАВКИ", [
        "2.1. Поставщик доставляет Товар своим транспортом на склад Покупателя по адресу: г. Энск, ул. Садовая, "
        "12, в течение 5 рабочих дней с даты оплаты заказа.",
        "2.2. Доставка, погрузка и разгрузка Товара оплачиваются Покупателем отдельно по тарифам Поставщика.",
        "2.3. Вместе с Товаром Поставщик передаёт универсальный передаточный документ (УПД), декларацию о "
        "соответствии, а для продукции животного происхождения — ветеринарные сопроводительные документы в "
        "системе «Меркурий».",
        "2.4. Право собственности и риск случайной гибели Товара переходят к Покупателю с момента подписания УПД.",
    ]),
    ("3. ЦЕНА И ПОРЯДОК РАСЧЁТОВ", [
        "3.1. Цена Товара указывается в Спецификации и включает НДС 22 %.",
        "3.2. Поставщик вправе в одностороннем порядке изменить цену Товара, уведомив Покупателя не менее чем "
        "за 5 календарных дней.",
        "3.3. Покупатель вносит 100 % предоплату каждой партии Товара в течение 3 банковских дней с даты "
        "выставления счёта.",
        "3.4. Оплата производится на расчётный счёт, указанный в счёте Поставщика.",
    ]),
    ("4. КАЧЕСТВО И ПРИЁМКА", [
        "4.1. Качество Товара должно соответствовать ГОСТ и техническим регламентам Таможенного союза, "
        "остаточный срок годности при поставке — не менее 50 %.",
        "4.2. Покупатель принимает Товар по количеству мест и внешнему виду при получении.",
        "4.3. Претензии по качеству Товара принимаются в течение 24 часов с момента приёмки.",
    ]),
    ("5. ОТВЕТСТВЕННОСТЬ СТОРОН", [
        "5.1. За просрочку поставки Поставщик уплачивает Покупателю неустойку 0,01 % от стоимости не "
        "поставленного в срок Товара за каждый день просрочки, но не более 1 % от его стоимости.",
        "5.2. За просрочку оплаты Покупатель уплачивает Поставщику пени 0,5 % от суммы задолженности за каждый "
        "день просрочки.",
        "5.3. Уплата неустойки не освобождает Стороны от исполнения обязательств по Договору.",
        "5.4. Поставщик не несёт ответственности за упущенную выгоду и иные убытки Покупателя, вызванные "
        "недопоставкой или просрочкой поставки Товара.",
    ]),
    ("6. ОБСТОЯТЕЛЬСТВА НЕПРЕОДОЛИМОЙ СИЛЫ", [
        "6.1. Стороны освобождаются от ответственности за неисполнение обязательств, вызванное обстоятельствами "
        "непреодолимой силы, если сообщили о них другой Стороне в течение 5 рабочих дней.",
    ]),
    ("7. РАЗРЕШЕНИЕ СПОРОВ", [
        "7.1. До обращения в суд Стороны направляют друг другу претензии, срок ответа на претензию — 10 рабочих "
        "дней.",
        "7.2. Споры рассматриваются в Арбитражном суде по месту нахождения Поставщика.",
    ]),
    ("8. СРОК ДЕЙСТВИЯ И РАСТОРЖЕНИЕ", [
        "8.1. Договор вступает в силу с даты подписания, действует до 31 декабря 2027 года и продлевается на "
        "каждый следующий календарный год, если ни одна из Сторон не заявит о его прекращении.",
        "8.2. Покупатель вправе отказаться от Договора только при отсутствии задолженности, письменно уведомив "
        "Поставщика за 90 календарных дней.",
    ]),
    ("9. ПРОЧИЕ УСЛОВИЯ", [
        "9.1. Документы, подписанные квалифицированной электронной подписью через оператора ЭДО, имеют силу "
        "оригиналов.",
        "9.2. Изменения и дополнения к Договору действительны, если составлены письменно и подписаны обеими "
        "Сторонами.",
    ]),
]  # fmt: skip


def make_contract(path: Path) -> None:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2)
        s.top_margin = s.bottom_margin = Cm(1.8)
    style = doc.styles["Normal"]
    style.font.name, style.font.size = "PT Sans", Pt(10.5)
    style.paragraph_format.space_after = Pt(4)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("ДОГОВОР ПОСТАВКИ № 31/27")
    r.bold, r.font.size = True, Pt(13)
    p = doc.add_paragraph("г. Энск\t\t\t\t\t\t\t\t«__» ноября 2026 г.")
    p = doc.add_paragraph(
        f"{SUPPLIER['full']} ({SUPPLIER['name']}), именуемое в дальнейшем «Поставщик», в лице генерального "
        "директора Соколова Игоря Петровича, действующего на основании Устава, с одной стороны, и "
        f"{BUYER['name']}, именуемое в дальнейшем «Покупатель», в лице директора Беловой Марины Андреевны, "
        "действующей на основании Устава, с другой стороны, заключили настоящий Договор о нижеследующем:"
    )
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for title, clauses in DRAFT:
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(8)
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        h.add_run(title).bold = True
        for c in clauses:
            doc.add_paragraph(c).alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(8)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h.add_run("10. АДРЕСА И РЕКВИЗИТЫ СТОРОН").bold = True
    # the supplier's account has a typo: one digit, so the control key with the БИК fails
    typo = SUPPLIER["account"][:-1] + "5"
    rows = [
        ("Поставщик:", "Покупатель:"),
        (SUPPLIER["name"], BUYER["name"]),
        (f"Адрес: {SUPPLIER['address']}", f"Адрес: {BUYER['address']}"),
        (f"ИНН {SUPPLIER['inn']}, КПП {SUPPLIER['kpp']}", f"ИНН {BUYER['inn']}, КПП {BUYER['kpp']}"),
        (f"ОГРН {SUPPLIER['ogrn']}", f"ОГРН {BUYER['ogrn']}"),
        (f"р/с {typo}", f"р/с {BUYER['account']}"),
        (f"в {SUPPLIER['bank']}", f"в {BUYER['bank']}"),
        (f"к/с {SUPPLIER['corr']}", f"к/с {BUYER['corr']}"),
        (f"БИК {SUPPLIER['bik']}", f"БИК {BUYER['bik']}"),
        ("Генеральный директор", "Директор"),
        (f"_____________ / {SUPPLIER['head']}", f"_____________ / {BUYER['head']}"),
    ]
    table = doc.add_table(rows=0, cols=2)
    for left, right in rows:
        cells = table.add_row().cells
        cells[0].text, cells[1].text = left, right
    doc.core_properties.author = "ООО «Зерновая линия»"
    doc.core_properties.title = "Договор поставки № 31/27 (проект)"
    doc.save(path)


# invoices -----------------------------------------------------------------------------------------

INVOICE_412 = {
    "number": "412",
    "date": "5 ноября 2026 г.",
    "due": "19.11.2026",
    "basis": "Договор поставки № 14/26 от 01.09.2026, заказ № З-118",
    # the supplier's account in this invoice is in another bank, not the one from the contract
    "bank": "АО «Тестовый банк»",
    "bik": "040000777",
    "corr": "30101810900000000777",
    "account": "40702810200000092615",
    "vat": 22,
    "lines": [
        ("Мука пшеничная хлебопекарная в/с, мешок 50 кг", 20, "меш", "2450.00", None),
        ("Мука ржаная обдирная, мешок 50 кг", 6, "меш", "2140.00", None),  # spec 1 980
        ("Масло сливочное 82,5 %, монолит 20 кг", 4, "кор", "18600.00", None),  # ordered 3
        ("Сахар белый, мешок 50 кг", 4, "меш", "3900.00", None),
        ("Дрожжи прессованные, коробка 10 кг", 2, "кор", "2100.00", "4400.00"),  # 2 × 2 100 is 4 200
        ("Яйцо куриное С0, коробка 360 шт", 5, "кор", "4680.00", None),
        ("Поддон деревянный, возвратная тара", 2, "шт", "450.00", None),  # not ordered, not in the spec
    ],
}
INVOICE_419 = {
    "number": "419",
    "date": "6 ноября 2026 г.",
    "due": "20.11.2026",
    "basis": "Договор поставки № 14/26 от 01.09.2026, заказ № З-121",
    "bank": SUPPLIER["bank"],
    "bik": SUPPLIER["bik"],
    "corr": SUPPLIER["corr"],
    "account": SUPPLIER["account"],
    "vat": 20,  # an old template: the rate is 22 % since 2026
    "lines": [
        ("Мука пшеничная цельнозерновая, мешок 25 кг", 8, "меш", "1650.00", None),
        ("Семечки подсолнечника очищенные, мешок 25 кг", 2, "меш", "4250.00", None),
        ("Лепестки миндальные, коробка 5 кг", 1, "кор", "7900.00", None),
        ("Соль поваренная пищевая, мешок 25 кг", 4, "меш", "520.00", None),
    ],
}


def make_invoice_pdf(inv: dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    pdfmetrics.registerFont(TTFont("PTSans", str(FONTS / "PT_Sans-Web-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("PTSans-Bold", str(FONTS / "PT_Sans-Web-Bold.ttf")))
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Счёт на оплату № {inv['number']}")
    c.setAuthor(SUPPLIER["name"])
    w, h = A4
    L, R = 40, w - 40

    def text(x, y, s, size=9, bold=False, right=False):
        c.setFont("PTSans-Bold" if bold else "PTSans", size)
        (c.drawRightString if right else c.drawString)(x, y, s)

    # bank block
    y = h - 50
    c.setLineWidth(0.6)
    c.rect(L, y - 66, R - L, 66)
    c.line(L + 300, y, L + 300, y - 66)
    c.line(L + 340, y, L + 340, y - 66)
    c.line(L, y - 33, R, y - 33)
    c.line(L + 300, y - 16, R, y - 16)
    text(L + 4, y - 12, inv["bank"])
    text(L + 4, y - 28, "Банк получателя", 7)
    text(L + 304, y - 12, "БИК")
    text(L + 344, y - 12, inv["bik"])
    text(L + 304, y - 28, "Сч. №")
    text(L + 344, y - 28, inv["corr"])
    text(L + 4, y - 45, f"ИНН {SUPPLIER['inn']}    КПП {SUPPLIER['kpp']}")
    text(L + 304, y - 45, "Сч. №")
    text(L + 344, y - 45, inv["account"])
    text(L + 4, y - 58, SUPPLIER["name"])
    text(L + 160, y - 58, "Получатель", 7)

    y -= 100
    text(L, y, f"Счёт на оплату № {inv['number']} от {inv['date']}", 14, True)
    c.setLineWidth(1.5)
    c.line(L, y - 8, R, y - 8)
    y -= 28
    text(L, y, f"Поставщик (Исполнитель): {SUPPLIER['name']}, ИНН {SUPPLIER['inn']}, КПП {SUPPLIER['kpp']},")
    text(L + 116, y - 12, SUPPLIER["address"])
    y -= 30
    text(L, y, f"Покупатель (Заказчик): {BUYER['name']}, ИНН {BUYER['inn']}, КПП {BUYER['kpp']}, {BUYER['address']}")
    y -= 18
    text(L, y, f"Основание: {inv['basis']}")

    # lines
    y -= 24
    cols = [L, L + 22, L + 330, L + 375, L + 410, L + 470, R]
    heads = ["№", "Товары (работы, услуги)", "Кол-во", "Ед.", "Цена", "Сумма"]
    c.setLineWidth(0.6)
    row_h = 16
    rows = len(inv["lines"]) + 1
    c.rect(L, y - row_h * rows, R - L, row_h * rows)
    for x in cols[1:-1]:
        c.line(x, y, x, y - row_h * rows)
    for i in range(1, rows):
        c.line(L, y - row_h * i, R, y - row_h * i)
    for i, head in enumerate(heads):
        text(cols[i] + 3, y - 11, head, 8, True)
    total = Decimal(0)
    for n, (name, qty, unit, price, printed) in enumerate(inv["lines"], 1):
        yy = y - row_h * n - 11
        price = Decimal(price)
        line_sum = Decimal(printed) if printed else price * qty
        total += line_sum
        text(cols[0] + 3, yy, str(n))
        text(cols[1] + 3, yy, name)
        text(cols[3] - 4, yy, str(qty), right=True)
        text(cols[3] + 3, yy, unit)
        text(cols[5] - 4, yy, fmt(price), right=True)
        text(cols[6] - 4, yy, fmt(line_sum), right=True)
    y -= row_h * rows + 18
    rate = inv["vat"]
    vat = (total * rate / (100 + rate)).quantize(Decimal("0.01"))
    for label, value in (("Итого:", total), (f"В том числе НДС ({rate}%):", vat), ("Всего к оплате:", total)):
        text(cols[5] - 4, y, label, 9, True, right=True)
        text(cols[6] - 4, y, fmt(value), 9, True, right=True)
        y -= 14
    y -= 6
    text(L, y, f"Всего наименований {len(inv['lines'])}, на сумму {fmt(total)} руб.")
    y -= 14
    text(L, y, words(total), 9, True)
    y -= 22
    text(
        L, y, f"Оплатить не позднее {inv['due']}. Оплата этого счёта означает согласие с условиями поставки товара.", 8
    )
    c.setLineWidth(1.5)
    c.line(L, y - 10, R, y - 10)
    y -= 40
    text(L, y, "Руководитель", 9, True)
    c.setLineWidth(0.5)
    c.line(L + 70, y - 2, L + 170, y - 2)
    text(L + 175, y, SUPPLIER["head"])
    text(L + 290, y, "Бухгалтер", 9, True)
    c.line(L + 345, y - 2, L + 445, y - 2)
    text(L + 450, y, SUPPLIER["accountant"])
    c.showPage()
    c.save()
    return buf.getvalue()


def scan(pdf: bytes, seed: int = 7) -> bytes:
    """A scan of a printed page: 200 dpi grey, a slight tilt, paper noise, JPEG, one picture per page."""
    import pypdfium2 as pdfium
    from PIL import Image, ImageFilter

    rnd = random.Random(seed)
    doc = pdfium.PdfDocument(pdf)
    img = doc[0].render(scale=200 / 72, grayscale=True).to_pil().convert("L")
    doc.close()
    img = img.rotate(0.6, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=255)
    px = img.load()
    for _ in range(img.width * img.height // 60):
        x, y = rnd.randrange(img.width), rnd.randrange(img.height)
        px[x, y] = max(0, px[x, y] - rnd.randrange(30, 90))
    img = img.filter(ImageFilter.GaussianBlur(0.5)).point(lambda v: int(v * 0.93 + 8))
    jpg = io.BytesIO()
    img.save(jpg, "JPEG", quality=72)
    out = io.BytesIO()
    Image.open(jpg).save(out, "PDF", resolution=200)
    return out.getvalue()


def main() -> int:
    OUT.mkdir(exist_ok=True)
    make_contract(OUT / "dogovor-postavki-31-27.docx")
    (OUT / "schet-412.pdf").write_bytes(make_invoice_pdf(INVOICE_412))
    (OUT / "schet-419-skan.pdf").write_bytes(scan(make_invoice_pdf(INVOICE_419)))
    for f in sorted(OUT.iterdir()):
        print(f"{f.name}: {f.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
