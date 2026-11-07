"""A contract: its clauses and fields, compared with the company's reference and checked by its rules.

1. The text is cut into numbered clauses ("3.3. Покупатель оплачивает..."), with the section title
   kept for each, and the requisites section is read party by party.
2. The clauses are paired with the reference clauses by the search core (meaning plus words), so a
   moved or renumbered clause still meets its reference.
3. A paired clause whose numbers differ from the reference is "changed"; a reference clause left
   without a pair is "missing"; a clause without a pair is "extra".
4. Every rule of the company runs over every clause; its finding says why it is a risk, and the
   fix is the rule's own wording or the paired reference clause.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from . import config
from .company import Company
from .engine.match import align
from .findings import Finding, number, verdict
from .requisites import Party, find

CLAUSE = re.compile(r"^\s*(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)\.?\s+(\S.*)$")
SECTION = re.compile(r"^\s*(?:#+\s*)?(\d{1,2})\.?\s+([А-ЯЁA-Z][^\d\n]{2,80})$")
REQUISITES = re.compile(r"реквизит|адреса\s+и\s+подписи|подписи\s+сторон", re.IGNORECASE)
MONTHS = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()
PARTY = re.compile(
    r"((?:ООО|АО|ПАО|ЗАО|НАО|ИП)\s*«[^»]{2,80}»|ИП\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.|\s+[А-ЯЁ][а-яё]+){0,2})"
    r"[^«]{0,300}?именуем\w*\s+в\s+дальнейшем\s+«([А-ЯЁ][а-яё]+)»",
    re.S,
)
NUM = re.compile(r"\d+(?:[.,]\d+)?")


@dataclass
class Clause:
    number: str
    section: str
    text: str  # without the number
    id: str = ""

    @property
    def passage(self) -> str:
        return f"{self.section}. {self.text}" if self.section else self.text


@dataclass
class Parsed:
    title: str
    number: str
    date: str
    city: str
    parties: list[Party]
    clauses: list[Clause]
    preamble: str


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip(" .;")


def parse(text: str) -> Parsed:
    lines = [line.strip() for line in text.splitlines()]
    clauses: list[Clause] = []
    section, preamble, req_lines = "", [], []
    in_requisites = False
    for raw in lines:
        line = raw.lstrip("#").strip()
        if not line:
            continue
        m_sec = SECTION.match(raw.lstrip("#").strip()) if not CLAUSE.match(line) else None
        if m_sec and len(line) < 90 and not line.endswith((",", ";")):
            section = m_sec.group(2).strip().rstrip(".")
            section = section[0] + section[1:].lower() if section.isupper() else section
            in_requisites = bool(REQUISITES.search(section))
            continue
        if not clauses and not in_requisites and REQUISITES.search(line) and len(line) < 60:
            in_requisites = True
            continue
        if in_requisites:
            req_lines.append(raw)
            continue
        m = CLAUSE.match(line)
        if m:
            clauses.append(Clause(m.group(1), section, m.group(2)))
        elif clauses:
            clauses[-1].text += " " + line  # a wrapped line of the clause above
        else:
            preamble.append(line)
    for i, c in enumerate(clauses, 1):
        c.text = re.sub(r"\s+", " ", c.text).strip()
        c.id = f"c{i}"

    head = "\n".join(preamble)
    title = next((p for p in preamble if re.match(r"договор", p, re.IGNORECASE)), "")
    num = re.search(r"№\s*([\w/\-]+)", title or head)
    return Parsed(
        title=re.sub(r"\s+", " ", title),
        number=num.group(1) if num else "",
        date=_date(head),
        city=_city(head),
        parties=_parties(head, "\n".join(req_lines)),
        clauses=clauses,
        preamble=head,
    )


def _date(text: str) -> str:
    m = re.search(r"«\s*(\d{1,2})\s*»\s*(" + "|".join(MONTHS) + r")\s+(\d{4})", text)
    if m:
        return f"{int(m.group(1)):02d}.{MONTHS.index(m.group(2)) + 1:02d}.{m.group(3)}"
    m = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", text)
    return m.group(1) if m else ""


def _city(text: str) -> str:
    m = re.search(r"\bг\.\s*([А-ЯЁ][а-яё\-]+)", text)
    return m.group(1) if m else ""


def _parties(preamble: str, requisites: str) -> list[Party]:
    parties = [Party(role=m.group(2), name=" ".join(m.group(1).split())) for m in PARTY.finditer(preamble)]
    if not requisites:
        return parties
    blocks = _requisite_blocks(requisites, parties)
    for p, block in zip(parties, blocks, strict=False):
        p.requisites = find(block)
    return parties


def _requisite_blocks(text: str, parties: list[Party]) -> list[str]:
    """One text per party: table columns side by side (DOCX, PDF layout) or blocks one after another."""
    rows = [line.split("\t") for line in text.splitlines() if line.strip()]
    if sum(1 for r in rows if len(r) >= 2) >= 3:
        width = max(len(r) for r in rows)
        return ["\n".join(r[i] for r in rows if i < len(r)) for i in range(width)]
    starts = []
    for p in parties:
        for key in (p.role, p.name):
            m = re.search(re.escape(key), text) if key else None
            if m:
                starts.append(m.start())
                break
        else:
            starts.append(-1)
    if any(s < 0 for s in starts):
        return [text] * len(parties) if len(parties) == 1 else []
    ordered = sorted(starts) + [len(text)]
    return [text[s : ordered[ordered.index(s) + 1]] for s in starts]


# the check ----------------------------------------------------------------------------------------


def _numbers(text: str) -> list[str]:
    return sorted(n.replace(",", ".") for n in NUM.findall(text))


def diff_words(old: str, new: str) -> list[list[str]]:
    """Word diff from the reference (old) to the clause (new): [["=", "text"], ["-", ...], ["+", ...]]."""
    a, b = old.split(), new.split()
    out: list[list[str]] = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "equal":
            out.append(["=", " ".join(a[i1:i2])])
        else:
            if i2 > i1:
                out.append(["-", " ".join(a[i1:i2])])
            if j2 > j1:
                out.append(["+", " ".join(b[j1:j2])])
    return out


def run_rules(company: Company, clause: Clause) -> list[Finding]:
    text = _norm(clause.text)
    out = []
    for rule in company.rules:
        if rule.scope_rx and not rule.scope_rx.search(text):
            continue
        m = rule.rx.search(text)
        hit = False
        if rule.check == "forbid":
            hit = bool(m)
        elif rule.check == "require":
            hit = not m
        elif m:
            value = float(m.group(1).replace(",", "."))
            hit = value > rule.limit if rule.check == "max" else value < rule.limit
        if hit:
            out.append(
                Finding(
                    level=rule.level,
                    kind="rule",
                    title=rule.title,
                    why=rule.why,
                    where=f"п. {clause.number}",
                    quote=clause.text,
                    fix=rule.fix,
                    rule=rule.id,
                    anchor=clause.id,
                )
            )
    return out


@dataclass
class ContractResult:
    doc: Parsed
    reference: Parsed
    findings: list[Finding]
    rows: list[dict] = field(default_factory=list)  # each clause with its status and pair

    def as_dict(self) -> dict:
        v = verdict(self.findings, "contract")
        d = self.doc
        return {
            "kind": "contract",
            "verdict": v.__dict__,
            "fields": [
                {"name": "Документ", "value": d.title or "Договор"},
                {"name": "Номер", "value": d.number or "не указан"},
                {"name": "Дата", "value": d.date or "не заполнена"},
                {"name": "Город", "value": d.city or "—"},
                *[
                    {"name": p.role or "Сторона", "value": p.name, "requisites": p.requisites.as_dict()}
                    for p in d.parties
                ],
                {"name": "Пунктов", "value": str(len(d.clauses))},
            ],
            "findings": [f.as_dict() for f in self.findings],
            "clauses": self.rows,
        }


def check(company: Company, embedder, text: str) -> ContractResult:
    doc = parse(text)
    ref = parse(company.reference_text)
    pairs = align(
        embedder,
        [c.passage for c in doc.clauses],
        [c.passage for c in ref.clauses],
        config.CLAUSE_MIN_DENSE,
        config.CLAUSE_MIN_LEXICAL,
    )
    pair_of = {p.left: p for p in pairs}
    paired_ref = {p.right for p in pairs}
    findings: list[Finding] = []
    rows = []

    for i, c in enumerate(doc.clauses):
        p = pair_of.get(i)
        r = ref.clauses[p.right] if p else None
        rule_hits = run_rules(company, c)
        for f in rule_hits:
            if not f.fix and r:
                f.fix, f.ref = r.text, r.number
        status = "extra"
        if r:
            if _norm(c.text) == _norm(r.text):
                status = "same"
            elif _numbers(c.text) != _numbers(r.text):
                status = "changed"
            else:
                status = "reworded"
        if status == "changed" and not rule_hits:
            findings.append(
                Finding(
                    level="low",
                    kind="changed",
                    title=f"Цифры отличаются от эталона (п. {r.number})",
                    why="Условие не нарушает правил компании, но сроки или суммы не те, что в эталоне. "
                    "Проверьте, что это согласовано.",
                    where=f"п. {c.number}",
                    quote=c.text,
                    fix=r.text,
                    ref=r.number,
                    anchor=c.id,
                )
            )
        if status == "extra" and not rule_hits:
            findings.append(
                Finding(
                    level="low",
                    kind="extra",
                    title="Пункта нет в эталоне",
                    why="Поставщик добавил условие, которого нет в договоре компании. Прочитайте его отдельно.",
                    where=f"п. {c.number}",
                    quote=c.text,
                    anchor=c.id,
                )
            )
        findings += rule_hits
        rows.append(
            {
                "id": c.id,
                "number": c.number,
                "section": c.section,
                "text": c.text,
                "status": status,
                "ref": r.number if r else "",
                "ref_text": r.text if r else "",
                "diff": diff_words(r.text, c.text) if r and status != "same" else [],
                "dense": round(p.dense, 3) if p else None,
                "lexical": round(p.lexical, 2) if p else None,
                "levels": sorted({f.level for f in rule_hits}),
            }
        )

    # reference clauses the contract dropped, placed after the clause that precedes them in the reference
    ref_to_doc = {p.right: p.left for p in pairs}
    for j, r in enumerate(ref.clauses):
        if j in paired_ref:
            continue
        prev = next((ref_to_doc[k] for k in range(j - 1, -1, -1) if k in ref_to_doc), None)
        findings.append(
            Finding(
                level="medium",
                kind="missing",
                title=f"Нет пункта эталона {r.number}",
                why=f"В договоре нет условия из раздела «{r.section}». Без него действует общее правило "
                "Гражданского кодекса, а оно может быть хуже для покупателя.",
                where=f"после п. {doc.clauses[prev].number}" if prev is not None else "в начале",
                fix=r.text,
                ref=r.number,
                anchor=doc.clauses[prev].id if prev is not None else "",
            )
        )

    for p in doc.parties:
        for problem in p.requisites.problems():
            findings.append(
                Finding(
                    level="high",
                    kind="requisites",
                    title=f"Ошибка в реквизитах: {p.role or p.name}",
                    why=f"{problem}. Платёж по такому счёту не дойдёт или уйдёт не туда.",
                    where="реквизиты",
                    quote=p.name,
                )
            )
    if not doc.date:
        findings.append(Finding(level="low", kind="field", title="Дата договора не заполнена", where="шапка"))

    # findings in the document's order within each level
    order = {c.id: i for i, c in enumerate(doc.clauses)}
    findings.sort(key=lambda f: order.get(f.anchor, len(order)))
    return ContractResult(doc, ref, number(findings), rows)
