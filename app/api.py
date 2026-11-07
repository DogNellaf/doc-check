"""HTTP API and the web page of the checker.

uvicorn app.api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import config
from .reader import ReadError
from .service import BusyError, CheckError, LimitError, Service, visitor_key

WEB = Path(__file__).resolve().parent.parent / "web"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app.state, "service"):
        from .setup import build

        app.state.service = build()
    yield


app = FastAPI(title="doc-check", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS, allow_methods=["GET", "POST"])


def _service(request: Request) -> Service:
    return request.app.state.service


def _visitor(request: Request) -> str:
    ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "")
    return visitor_key(f"ip:{ip}")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/examples")
def examples(request: Request):
    s = _service(request)
    return {"examples": s.example_list(), "remaining": s.remaining(_visitor(request)), "limit": config.CHECKS_PER_DAY}


@app.get("/api/examples/{name}")
def example(name: str, request: Request):
    r = _service(request).examples.get(name)
    if r is None:
        return JSONResponse({"error": "Такого примера нет."}, status_code=404)
    return r


@app.get("/api/company")
def company(request: Request):
    return _service(request).company_info()


@app.post("/api/check")
async def check(request: Request, file: UploadFile = File(...)):
    s = _service(request)
    visitor = _visitor(request)
    data = await file.read(config.UPLOAD_MAX_BYTES + 1)
    try:
        result = await s.check_upload(visitor, file.filename or "document", data)
    except LimitError as e:
        return JSONResponse({"error": str(e), "kind": "limit", "remaining": 0}, status_code=429)
    except BusyError as e:
        return JSONResponse({"error": str(e), "kind": "busy"}, status_code=503)
    except (CheckError, ReadError) as e:
        return JSONResponse({"error": str(e), "remaining": s.remaining(visitor)}, status_code=400)
    except Exception:
        log.exception("check failed: %s", file.filename)
        return JSONResponse({"error": "Не получилось проверить файл, попробуйте другой."}, status_code=500)
    return {**result, "remaining": s.remaining(visitor)}


@app.get("/api/report/{rid}.{fmt}")
def download(rid: str, fmt: str, request: Request):
    if fmt not in TYPES:
        return JSONResponse({"error": "Есть только xlsx и docx."}, status_code=404)
    out = _service(request).report(rid, fmt)
    if out is None:
        return JSONResponse(
            {"error": "Отчёт устарел: файлы хранятся час. Проверьте документ ещё раз."}, status_code=404
        )
    data, name = out
    return Response(
        data,
        media_type=TYPES[fmt],
        headers={"Content-Disposition": f"attachment; filename=\"report.{fmt}\"; filename*=UTF-8''{quote(name)}"},
    )


app.mount("/examples", StaticFiles(directory=config.EXAMPLES_DIR), name="examples")
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
