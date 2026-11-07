"""One document from bytes to a result and its two reports.

The same steps serve a visitor's upload (in a child process, worker.py) and the examples (checked
once when the image is built, precompute.py): read the text, tell a contract from an invoice, check
it, and write the Excel report and the Word file. The heavy libraries (pypdf, pypdfium2, Tesseract,
python-docx, openpyxl) are imported only here, so the web process never loads them.
"""

from __future__ import annotations

import re

from . import contract, invoice, llm, report
from .company import Company
from .reader import read


class CheckError(ValueError):
    pass


def detect(text: str) -> str:
    head = text[:2500]
    if re.search(r"сч[её]т\s+(?:на\s+оплату\s+)?№", head, re.IGNORECASE):
        return "invoice"
    clauses = sum(1 for line in text.splitlines() if contract.CLAUSE.match(line))
    if re.search(r"договор", head, re.IGNORECASE) and clauses >= 3:
        return "contract"
    raise CheckError("Это не похоже на договор или счёт на оплату. Пришлите договор с пунктами 1.1, 1.2… или счёт.")


def check(company: Company, filename: str, data: bytes, model=None) -> tuple[dict, int]:
    """The result as the API returns it and the model tokens spent (0 without a model)."""
    doc = read(filename, data)
    kind = detect(doc.text)
    tokens = 0
    if kind == "contract":
        result = contract.check(company, doc.text).as_dict()
    else:
        model_lines = None
        if model is not None and not invoice.parse_invoice(doc.text).lines:
            try:
                model_lines, tokens = llm.extract_lines(model, doc.text)
            except llm.LLMError:
                model_lines = None
        result = invoice.check(company, doc.text, model_lines).as_dict()
    result.update(file=filename, fmt=doc.fmt, pages=doc.pages, ocr=doc.ocr)
    return result, tokens


def reports(result: dict, company: Company) -> dict[str, tuple[bytes, str]]:
    """{"xlsx": (bytes, file name), "docx": (bytes, file name)}."""
    stem = re.sub(r"\.[a-z]+$", "", result.get("file", "document"), flags=re.IGNORECASE)
    if result["kind"] == "contract":
        docx = report.contract_docx(result), f"{stem}-правки.docx"
    else:
        docx = report.invoice_docx(result, company.name), f"{stem}-письмо.docx"
    return {"xlsx": (report.xlsx(result), f"{stem}-проверка.xlsx"), "docx": docx}
