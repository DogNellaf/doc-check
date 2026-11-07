# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-07

### Added

- Contract check: clauses paired with the company's reference contract by the ai-consultant engine
  (multilingual-e5-small plus words weighted by rarity), changed, missing and extra clauses, and the
  lawyer's rules from `rules.toml` with the reason and the fix for each finding.
- Invoice check: line arithmetic, totals, VAT rate and amount, the amount in words, the payee's
  requisites against the supplier's contract, the basis, prices against the agreed price list and
  quantities against the order, with a guard on pack sizes.
- Control digits of ИНН, ОГРН and accounts, an account checked together with the bank's БИК.
- Reading of PDF, DOCX, TXT and scans: Tesseract on the server with the table borders removed first.
- Reports: Excel with every finding and row; Word with the contract's tracked changes and comments,
  or a letter to the supplier about the invoice.
- An optional model (GigaChat or an OpenAI-compatible API) that reads invoice lines the rules cannot
  find, with a queue and a daily token budget.
- A web page on the Tabler dashboard layout with three examples (a draft contract, an invoice and a
  scanned invoice) and an upload, and sidebar pages with the reference contract, the lawyer's rules,
  suppliers with their price lists and the orders. 10 checks of own files per visitor a day, uploads
  kept in memory for an hour.
- The acceptance test on the real model: 25 of 25 planted problems found, no findings on the
  reference contract and on a clean invoice.
