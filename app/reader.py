"""The text of an uploaded document: PDF, a scan, DOCX or plain text.

A PDF is read from its text layer first. When a page has no text, it is a scan: the page is
rendered at 300 dpi and read by Tesseract (rus+eng), locally, nothing leaves the server. A photo
or a scan in JPG or PNG goes the same way. DOCX gives paragraphs and table rows in document
order, a row with its cells separated by tabs, so an invoice table reads like the PDF one.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass

from . import config


class ReadError(ValueError):
    pass


@dataclass
class Text:
    text: str
    pages: int
    ocr: bool  # at least one page was read by OCR
    fmt: str  # pdf | docx | txt | image


IMAGE = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp")


def read(filename: str, data: bytes) -> Text:
    name = filename.lower()
    if len(data) > config.UPLOAD_MAX_BYTES:
        raise ReadError(f"Файл больше {config.UPLOAD_MAX_BYTES // 1_000_000} МБ, пришлите поменьше.")
    if not data:
        raise ReadError("Файл пустой.")
    if name.endswith(".pdf"):
        out = _pdf(data)
    elif name.endswith(".docx"):
        out = _docx(data)
    elif name.endswith((".txt", ".md")):
        out = Text(_decode(data), 1, False, "txt")
    elif name.endswith(IMAGE):
        out = Text(ocr_image(_open_image(data)), 1, True, "image")
    else:
        raise ReadError("Подойдёт PDF, скан в JPG или PNG, DOCX или TXT.")
    out.text = normalize(out.text)
    if len(out.text) < 40:
        raise ReadError("В файле почти нет текста: возможно, скан слишком бледный или это не документ.")
    out.text = out.text[: config.MAX_CHARS]
    return out


def normalize(text: str) -> str:
    text = text.replace(" ", " ").replace(" ", " ").replace("\r", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "cp1251"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ReadError("Не получилось прочитать текст, сохраните его в UTF-8.")


def _pdf(data: bytes) -> Text:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ReadError("PDF защищён паролем.")
        n = len(reader.pages)
        if n > config.MAX_PAGES:
            raise ReadError(f"В PDF больше {config.MAX_PAGES} страниц, пришлите покороче.")
        texts = [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]
    except PdfReadError as e:
        raise ReadError("Не получилось прочитать PDF.") from e
    scanned = [i for i, t in enumerate(texts) if len(t.strip()) < 30]  # no text layer
    if len(scanned) > config.OCR_MAX_PAGES:
        raise ReadError(f"В скане больше {config.OCR_MAX_PAGES} страниц, пришлите первые страницы отдельно.")
    for i in scanned:
        texts[i] = ocr_pdf_page(data, i)
    ocr = bool(scanned)
    return Text("\n\n".join(_layout(t) for t in texts), n, ocr, "pdf")


def _layout(text: str) -> str:
    """pypdf's layout mode keeps the columns with runs of spaces; three or more become a tab."""
    lines = [re.sub(r" {3,}", "\t", line.strip()) for line in text.splitlines()]
    return "\n".join(lines)


def _docx(data: bytes) -> Text:
    from docx import Document
    from docx.oxml.ns import qn

    try:
        doc = Document(io.BytesIO(data))
    except Exception as e:  # python-docx raises several kinds for a broken file
        raise ReadError("Не получилось прочитать DOCX.") from e
    lines = []
    for block in doc.element.body.iterchildren():
        if block.tag == qn("w:p"):
            lines.append("".join(t.text or "" for t in block.iter(qn("w:t"))))
        elif block.tag == qn("w:tbl"):
            for row in block.iter(qn("w:tr")):
                cells = [
                    " ".join("".join(t.text or "" for t in p.iter(qn("w:t"))) for p in c.iter(qn("w:p"))).strip()
                    for c in row.iter(qn("w:tc"))
                ]
                lines.append("\t".join(cells))
    return Text("\n".join(lines), 1, False, "docx")


# OCR ------------------------------------------------------------------------------------------


def _open_image(data: bytes):
    from PIL import Image, UnidentifiedImageError

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        raise ReadError("Не получилось открыть картинку.") from e
    if img.width * img.height > 40_000_000:
        raise ReadError("Картинка слишком большая, хватит 300 dpi.")
    return img


def ocr_pdf_page(data: bytes, index: int) -> str:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(data)
    try:
        img = pdf[index].render(scale=300 / 72, grayscale=True).to_pil()
    finally:
        pdf.close()
    return ocr_image(img)


def ocr_image(img) -> str:
    import pytesseract
    from PIL import ImageOps

    img = without_rules(ImageOps.exif_transpose(img).convert("L"))
    try:
        # psm 6: one uniform block, keeps table rows on one line; preserve spaces between columns
        text = pytesseract.image_to_string(
            img, lang=config.OCR_LANG, config="--psm 6 -c preserve_interword_spaces=1", timeout=config.OCR_TIMEOUT
        )
    except pytesseract.TesseractNotFoundError as e:
        raise ReadError("Распознавание сканов на этом сервере не установлено (нужен Tesseract).") from e
    except RuntimeError as e:  # timeout
        raise ReadError("Скан распознаётся слишком долго, пришлите страницу почётче.") from e
    return fix_ocr(_layout(text))


def _long_runs(dark, length: int):
    """Pixels that belong to a run of at least `length` dark pixels along each row."""
    import numpy as np

    h, w = dark.shape
    if w < length:
        return np.zeros_like(dark)
    cs = np.cumsum(np.pad(dark.astype(np.int32), ((0, 0), (1, 0))), axis=1)
    full = (cs[:, length:] - cs[:, :-length]) == length  # a fully dark window starts here
    fc = np.cumsum(np.pad(full.astype(np.int32), ((0, 0), (1, 0))), axis=1)
    j = np.arange(w)
    hi, lo = np.minimum(j + 1, w - length + 1), np.maximum(j - length + 1, 0)
    return (fc[:, hi] - fc[:, lo]) > 0


_BAND = 256


def without_rules(img):
    """Table borders turned white. Tesseract reads the grid of an invoice as "|", "[" and lost digits;
    a letter has no stroke that long, so only the lines go. Scale-aware: lengths are for 300 dpi."""
    import numpy as np
    from PIL import Image

    a = np.asarray(img)
    dark = a < 150
    scale = img.width / 2480  # A4 at 300 dpi
    h_len, v_len = max(20, int(90 * scale)), max(20, int(60 * scale))
    # in bands of rows (and of columns for the vertical lines): the cumulative sums of a whole A4
    # page at 300 dpi would take ~150 MB at once, a band of 256 takes a few
    lines = np.zeros_like(dark)
    for r in range(0, dark.shape[0], _BAND):
        lines[r : r + _BAND] |= _long_runs(dark[r : r + _BAND], h_len)
    for c in range(0, dark.shape[1], _BAND):
        lines[:, c : c + _BAND] |= _long_runs(dark[:, c : c + _BAND].T, v_len).T
    # the antialiased edges of a line go too
    lines = lines | np.roll(lines, 1, 0) | np.roll(lines, -1, 0) | np.roll(lines, 1, 1) | np.roll(lines, -1, 1)
    out = a.copy()
    out[lines] = 255
    return Image.fromarray(out)


def fix_ocr(text: str) -> str:
    """Frequent OCR slips in Russian documents: "000 «" for "ООО «", spaces inside long account numbers."""
    text = re.sub(r"\b0{3}(?=\s*«)", "ООО", text)
    text = re.sub(r"\b0(?=А\s*«)", "О", text)

    # 20 digits of an account split into a few groups: "40702810000000017 384"
    def join(m):
        return m.group(1).replace(" ", "") if m.group(1).count(" ") <= 2 else m.group(1)

    return re.sub(r"(?<!\d)((?:\d ?){19}\d)(?!\d)", join, text)
