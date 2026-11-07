import io

import pytest
from fastapi.testclient import TestClient

from app import config
from app.setup import build

from .conftest import FakeEmbedder, example


@pytest.fixture
def client(fake_thresholds, monkeypatch):
    monkeypatch.setattr(config, "CHECKS_PER_DAY", 2)
    from app.api import app

    app.state.service = build(embedder=FakeEmbedder(), model=None)
    with TestClient(app) as c:
        yield c
    del app.state.service


def test_examples_are_ready_and_free(client):
    data = client.get("/api/examples").json()
    ready = {e["id"] for e in data["examples"] if e["ready"]}
    assert {"contract", "invoice"} <= ready
    assert data["remaining"] == 2
    r = client.get("/api/examples/contract").json()
    assert r["kind"] == "contract" and r["id"] == "example-contract"
    assert client.get("/api/examples").json()["remaining"] == 2  # examples do not count


def test_upload_limit_and_reports(client):
    files = {"file": ("dogovor.docx", example("dogovor-postavki-31-27.docx"))}
    r = client.post("/api/check", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "contract" and body["remaining"] == 1

    x = client.get(f"/api/report/{body['id']}.xlsx")
    assert x.status_code == 200
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(x.content))
    assert wb.sheetnames == ["Итог", "Замечания", "Пункты"]
    assert wb["Итог"]["B2"].value == body["verdict"]["text"]

    d = client.get(f"/api/report/{body['id']}.docx")
    assert d.status_code == 200
    import zipfile

    z = zipfile.ZipFile(io.BytesIO(d.content))
    xml = z.read("word/document.xml").decode()
    assert "<w:ins " in xml and "<w:del " in xml and "w:delText" in xml
    assert "word/comments.xml" in z.namelist()
    assert "Предоплата больше 30 %" in z.read("word/comments.xml").decode()

    client.post("/api/check", files={"file": ("s.pdf", example("schet-412.pdf"))})
    r = client.post("/api/check", files=files)
    assert r.status_code == 429
    assert "лимит" in r.json()["error"]


def test_invoice_letter(client):
    d = client.get("/api/report/example-invoice.docx")
    assert d.status_code == 200
    from docx import Document

    text = "\n".join(p.text for p in Document(io.BytesIO(d.content)).paragraphs)
    assert "Кому: ООО «Зерновая линия»" in text
    assert "Реквизиты не совпадают с договором" in text


def test_bad_files(client):
    r = client.post("/api/check", files={"file": ("a.exe", b"MZ\x90\x00" * 20)})
    assert r.status_code == 400 and "PDF" in r.json()["error"]
    r = client.post(
        "/api/check", files={"file": ("note.txt", "Купить хлеба и молока, позвонить маме вечером.".encode())}
    )
    assert r.status_code == 400 and "не похоже" in r.json()["error"].lower()
    assert client.get("/api/report/nope.xlsx").status_code == 404
    assert client.get("/api/report/example-contract.pdf").status_code == 404


def test_company_info(client):
    co = client.get("/api/company").json()
    assert co["name"] == "ООО «Колосок»"
    assert len(co["reference"]) == 25 and len(co["rules"]) == 14
    assert co["suppliers"][0]["contract"] == "№ 14/26 от 01.09.2026"
