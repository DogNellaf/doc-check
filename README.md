# doc-check

English · [Русский](README.ru.md)

A checker for supply contracts and invoices, built on the search engine of
[ai-consultant](https://github.com/DogNellaf/ai-consultant). A contract from a supplier is compared
clause by clause with the company's reference contract and checked by its lawyer's rules. An invoice
is checked against its own arithmetic, the supplier's contract, the agreed price list and the order.
The result is a verdict, a list of findings with the reason for each, an Excel report, and a Word file:
the contract with tracked changes and comments, or a letter to the supplier about the invoice.

The demo company is Kolosok, the made-up bakery from ai-consultant, now as a buyer of flour,
butter and eggs. Its supplier, people and requisites are made up too.

## Quick start

```bash
docker compose up --build
```

Open http://localhost:8000/. Three examples are checked at start, and you can upload your own PDF,
scan (JPG, PNG or a PDF of pictures), DOCX or TXT. Nothing to configure: no model key is needed.

## What it checks

**A contract** (DOCX, PDF, a scan)

1. The text is cut into numbered clauses (`3.3. Покупатель оплачивает…`) with their section titles;
   the parties come from the preamble ("именуемое в дальнейшем «Поставщик»"), their requisites from
   the requisites section, a two-column table or blocks one after another.
2. Each clause is paired with a reference clause by the ai-consultant engine: the meaning
   (multilingual-e5-small) plus the shared words weighted by rarity. A pair counts only when both pass
   their thresholds, so a renumbered clause still finds its reference and a new one stays new.
3. A paired clause with other numbers is "changed", a reference clause without a pair is "missing"
   (the Word file puts it back as an insertion), a clause without a pair is "extra".
4. Every rule from `knowledge/kolosok/rules.toml` runs over every clause: prepayment above 30 %, a
   buyer's penalty above 0.1 % a day or without a cap, a unilateral price change, payment to "the
   account in the invoice", claims within hours, the supplier's court, and others. A rule is a regular
   expression, a check (`forbid`, `require`, `max`, `min`) and the reason in words; a lawyer edits the
   file, not the code.
5. ИНН, ОГРН and accounts are checked by their control digits, an account together with the bank's БИК.

**An invoice** (PDF from an accounting program, a scan)

- quantity × price for every line, the lines against "Итого", VAT at the right rate (22 % since 2026)
  and the right amount, "Всего к оплате", the amount in words against the digits;
- the payee's requisites against the supplier's contract: another account or bank is the main
  sign of a forged invoice;
- the basis: the contract number and the order;
- every line against the agreed price list and against the order, paired by the same engine, with
  a guard on pack sizes and fat ("мешок 25 кг" is not "мешок 50 кг", "72,5 %" is not "82,5 %").

The examples carry 25 planted problems; the acceptance test (`tests/test_smoke.py`, on the real model)
finds all 25 and nothing on the reference contract checked against itself or on a clean invoice.

## Scans

A page without a text layer is rendered at 300 dpi and read by Tesseract (rus+eng) on the server.
Table borders are removed first: Tesseract reads a grid as `|` and `[` and loses the digits next to it.
Common slips are fixed after: `000 «` for `ООО «`, a space inside a 20-digit account. A scan of the
example invoice is read in about 5 seconds.

## Model

`LLM_PROVIDER=none` (default), `gigachat` or `openai`, behind one `complete()` call (`app/llm.py`)
as in ai-consultant. Every check is made by code; the model has one job: when the rules find no lines
in an invoice (an unusual layout, a bad scan), it reads them out as JSON, and the code checks them
like any others. A model mistake then shows up as a mismatch, not as a wrong "all good". GigaChat
terms: the freemium for individuals is for personal non-commercial use only.

## Limits

| Setting | Default | What happens |
|---|---|---|
| `CHECKS_PER_DAY` | 10 | own files per visitor (IP, salted hash) a day; the examples are free |
| `WORK_CONCURRENCY` | 1 | checks at once, the rest wait in a queue |
| `QUEUE_MAX` | 20 | more waiting and the visitor is asked to repeat in a minute |
| `DAILY_TOKEN_BUDGET` | 200 000 | the model is off for the rest of the day |
| `UPLOAD_MAX_BYTES` | 5 MB | and `MAX_PAGES` 15 |
| `RESULT_TTL` | 3600 | seconds a report stays downloadable |

## Data

Uploaded files are not stored: the text and the report live in memory for an hour, for the downloads.
The image writes nothing to disk. The demo company, its supplier and every number are made up;
requisites use region code 00, which no tax office has, so they cannot belong to a real company,
though their control digits are right (except the ones the examples get wrong on purpose).

## Your company

`COMPANY_DIR` holds plain files:

- `company.toml`: the company, its VAT rate, its requisites and the suppliers with signed contracts;
- `reference-supply.md`: the reference contract, `## ` sections and numbered clauses;
- `rules.toml`: the lawyer's rules;
- `spec-*.csv`: the price list agreed with a supplier, `name;unit;price`;
- `orders/*.csv`: orders, `name;unit;qty`, with the number and date in the first comment line.

## Development

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt -r requirements-dev.txt
python scripts/download_model.py
python scripts/make_examples.py          # rebuilds examples/ (reportlab, PT Sans under OFL)
pytest                                   # the OCR tests need tesseract with rus
ruff check . && ruff format --check .
```

The page is built on [Tabler](https://tabler.io) 1.6.1 (MIT) with [Lucide](https://lucide.dev)
icons (ISC), served from the app. The example PDFs use PT Sans by ParaType (OFL).

## License

MIT
