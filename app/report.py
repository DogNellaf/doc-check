"""Reports to download: Excel with every finding and row, Word with the edits.

For a contract the Word file is the contract itself with tracked changes, as a lawyer would send
it back: the risky words are struck out and the reference wording is inserted word by word, a
comment beside each clause says why, and a dropped reference clause comes back as an insertion.
The supplier accepts or rejects each change in Word. For an invoice it is a letter to the
supplier listing what to correct.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime

from .findings import LEVEL_NAMES

AUTHOR = "Проверка договоров"
FILL = {"high": "F8D7DA", "medium": "FFF3CD", "low": "E2E3E5", "ok": "D1E7DD"}


# Excel --------------------------------------------------------------------------------------------


def xlsx(result: dict) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    bold = Font(bold=True)
    wrap = Alignment(wrap_text=True, vertical="top")

    def sheet(ws, head: list[str], rows: list[list], widths: list[int], level_col: int | None = None):
        ws.append(head)
        for c in ws[1]:
            c.font = bold
        for r in rows:
            ws.append(r)
            if level_col is not None and r[level_col] in LEVEL_NAMES.values():
                level = next(k for k, v in LEVEL_NAMES.items() if v == r[level_col])
                for c in ws[ws.max_row]:
                    c.fill = PatternFill("solid", fgColor=FILL[level])
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = wrap
        ws.freeze_panes = "A2"

    v = result["verdict"]
    ws = wb.active
    ws.title = "Итог"
    ws.append(["Файл", result.get("file", "")])
    ws.append(["Вывод", v["text"]])
    ws["B2"].fill = PatternFill("solid", fgColor=FILL[v["level"]])
    ws["B2"].font = bold
    for lv, n in v["counts"].items():
        ws.append([LEVEL_NAMES[lv], n])
    ws.append([])
    for f in result["fields"]:
        ws.append([f["name"], f["value"]])
        req = f.get("requisites") or {}
        for key, label in (("inn", "ИНН"), ("kpp", "КПП"), ("ogrn", "ОГРН"), ("account", "Р/с"), ("bank", "Банк"),
                           ("bik", "БИК"), ("corr_account", "К/с")):  # fmt: skip
            if req.get(key):
                ws.append([f"  {label}", req[key]])
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 90
    for c in ws["A"]:
        c.font = bold

    sheet(
        wb.create_sheet("Замечания"),
        ["Уровень", "Где", "Что", "Почему", "Документ", "Как должно быть"],
        [[LEVEL_NAMES[f["level"]], f["where"], f["title"], f["why"], f["quote"], f["fix"]] for f in result["findings"]],
        [18, 14, 40, 60, 50, 50],
        level_col=0,
    )
    if result["kind"] == "invoice":
        rows = []
        for r in result["lines"]:
            worst = next((lv for lv in ("high", "medium", "low") if lv in r["issues"]), "")
            rows.append([r["n"], r["name"], r["qty"], r["unit"], r["price"], r["total"],
                         (r.get("spec") or {}).get("price", "нет"), r.get("ordered", "нет"),
                         LEVEL_NAMES.get(worst, "")])  # fmt: skip
        sheet(
            wb.create_sheet("Строки"),
            ["№", "Наименование", "Кол-во", "Ед.", "Цена", "Сумма", "Цена по спецификации", "В заказе", "Замечание"],
            rows,
            [5, 48, 9, 7, 13, 14, 20, 10, 18],
            level_col=8,
        )
    else:
        status = {"same": "как в эталоне", "reworded": "другая формулировка", "changed": "другие цифры",
                  "extra": "нет в эталоне"}  # fmt: skip
        sheet(
            wb.create_sheet("Пункты"),
            ["Пункт", "Раздел", "Сверка", "Текст договора", "Пункт эталона", "Текст эталона"],
            [
                [c["number"], c["section"], status[c["status"]], c["text"], c["ref"], c["ref_text"]]
                for c in result["clauses"]
            ],  # fmt: skip
            [7, 24, 18, 70, 8, 70],
        )
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


# Word ---------------------------------------------------------------------------------------------


class _Revisions:
    """w:ins and w:del around python-docx runs, with ids unique in the document."""

    def __init__(self):
        self.next_id = 1000
        self.date = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def wrap(self, run, tag: str):
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn

        el = OxmlElement(f"w:{tag}")
        el.set(qn("w:id"), str(self.next_id))
        el.set(qn("w:author"), AUTHOR)
        el.set(qn("w:date"), self.date)
        self.next_id += 1
        r = run._r
        if tag == "del":
            for t in r.findall(qn("w:t")):
                t.tag = qn("w:delText")
        r.addprevious(el)
        el.append(r)
        return el

    def mark_paragraph_inserted(self, paragraph):
        """The paragraph mark itself is inserted too, so rejecting the change removes the whole paragraph."""
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn

        ppr = paragraph._p.get_or_add_pPr()
        rpr = ppr.find(qn("w:rPr"))
        if rpr is None:
            rpr = OxmlElement("w:rPr")
            ppr.append(rpr)
        ins = OxmlElement("w:ins")
        ins.set(qn("w:id"), str(self.next_id))
        ins.set(qn("w:author"), AUTHOR)
        ins.set(qn("w:date"), self.date)
        self.next_id += 1
        rpr.append(ins)


def _diff(old: str, new: str) -> list[tuple[str, str]]:
    import difflib

    a, b = old.split(" "), new.split(" ")
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(("=", " ".join(a[i1:i2])))
            continue
        if i2 > i1:
            out.append(("-", " ".join(a[i1:i2])))
        if j2 > j1:
            out.append(("+", " ".join(b[j1:j2])))
    return out


def _document():
    from docx import Document
    from docx.shared import Cm, Pt

    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2)
    style = doc.styles["Normal"]
    style.font.name, style.font.size = "PT Sans", Pt(10.5)
    style.paragraph_format.space_after = Pt(4)
    return doc


def contract_docx(result: dict) -> bytes:
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = _document()
    rev = _Revisions()
    title = next((f["value"] for f in result["fields"] if f["name"] == "Документ"), "Договор")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(title).bold = True
    v = result["verdict"]
    doc.add_paragraph(
        f"Правки внесены в режиме рецензирования по эталону и правилам компании. Вывод: {v['text']}. "
        f"Критично — {v['counts']['high']}, согласовать — {v['counts']['medium']}, "
        f"обратить внимание — {v['counts']['low']}."
    ).runs[0].italic = True

    by_clause: dict[str, list[dict]] = {}
    missing_after: dict[str, list[dict]] = {}
    for f in result["findings"]:
        if f["kind"] == "missing":
            missing_after.setdefault(f["anchor"], []).append(f)
        elif f["anchor"]:
            by_clause.setdefault(f["anchor"], []).append(f)

    def insert_missing(anchor: str):
        for f in missing_after.get(anchor, []):
            para = doc.add_paragraph()
            rev.mark_paragraph_inserted(para)
            run = para.add_run(f"{f['ref']}. {f['fix']}")
            # the comment first: its range marks stay outside the insertion that wraps the run
            doc.add_comment(run, text=f"{f['title']}. {f['why']}", author=AUTHOR, initials="ПД")
            rev.wrap(run, "ins")

    insert_missing("")
    section = None
    for c in result["clauses"]:
        if c["section"] and c["section"] != section:
            section = c["section"]
            h = doc.add_paragraph()
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            h.add_run(section).bold = True
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        num = para.add_run(f"{c['number']}. ")
        found = by_clause.get(c["id"], [])
        fix = next((f["fix"] for f in found if f["fix"]), "")
        if fix and fix != c["text"]:
            for op, text in _diff(c["text"], fix):
                run = para.add_run(text + " ")
                if op == "-":
                    rev.wrap(run, "del")
                elif op == "+":
                    rev.wrap(run, "ins")
        else:
            para.add_run(c["text"])
        if found:
            note = "\n\n".join(f"{LEVEL_NAMES[f['level']]}: {f['title']}. {f['why']}".strip() for f in found)
            doc.add_comment(num, text=note, author=AUTHOR, initials="ПД")
        insert_missing(c["id"])

    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


def invoice_docx(result: dict, company: str) -> bytes:
    from docx.shared import Pt

    doc = _document()
    fields = {f["name"]: f["value"] for f in result["fields"]}
    supplier = fields.get("Поставщик", "").split(",")[0]
    doc.add_paragraph(f"Кому: {supplier}\nОт: {company}")
    p = doc.add_paragraph()
    r = p.add_run(f"О расхождениях в документе «{fields.get('Документ', 'Счёт')}» от {fields.get('Дата', '')}")
    r.bold, r.font.size = True, Pt(12)
    doc.add_paragraph(
        "Добрый день! Перед оплатой мы сверили счёт с договором, спецификацией и заказом и нашли расхождения. "
        "Просим выставить исправленный счёт:"
    )
    to_fix = [f for f in result["findings"] if f["level"] in ("high", "medium")]
    for f in to_fix:
        item = doc.add_paragraph(style="List Number")
        item.add_run(f"{f['title']}. ").bold = True
        item.add_run(f["why"])
    notes = [f for f in result["findings"] if f["level"] == "low"]
    if notes:
        doc.add_paragraph("Просим также уточнить:")
        for f in notes:
            doc.add_paragraph(f"{f['title']}. {f['why']}", style="List Bullet")
    if not to_fix and not notes:
        doc.add_paragraph("Расхождений не нашли, счёт принят к оплате.")
    doc.add_paragraph("\nС уважением,\nотдел закупок " + company)
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()
