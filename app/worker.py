"""A visitor's document is checked in a child process that exits right after.

Reading a scan renders pages at 300 dpi and runs Tesseract, a PDF pulls in pypdf and pdfium, the
reports pull in python-docx and openpyxl. In one long-lived process all of that would stay in
memory after the first upload. Here it lives only for the seconds of one check: the child does the
work, sends back the result and the two reports, and exits, so the web process stays at its idle
size between checks. A child that runs out of time or memory is killed, and the visitor gets a
plain message instead of a hung request.

On Linux the children are forked from a small fork server started once, so a check does not pay
for starting Python again; elsewhere (Windows, tests) they are spawned.
"""

from __future__ import annotations

import logging
import multiprocessing as mp

from . import config

log = logging.getLogger(__name__)

_CTX = mp.get_context("forkserver" if "forkserver" in mp.get_all_start_methods() else "spawn")


class WorkerError(RuntimeError):
    """The check failed: kind is "check" or "read" for the visitor's file, "crash" for the child."""

    def __init__(self, message: str, kind: str):
        super().__init__(message)
        self.kind = kind


def _child(conn, filename: str, data: bytes, use_model: bool) -> None:
    from . import llm, pipeline
    from .company import load
    from .reader import ReadError

    try:
        company = load(config.COMPANY_DIR)
        model = llm.from_config() if use_model else None
        result, tokens = pipeline.check(company, filename, data, model)
        conn.send({"result": result, "reports": pipeline.reports(result, company), "tokens": tokens})
    except ReadError as e:
        conn.send({"error": str(e), "kind": "read"})
    except pipeline.CheckError as e:
        conn.send({"error": str(e), "kind": "check"})
    except Exception as e:  # noqa: BLE001 - the parent logs it and answers the visitor plainly
        conn.send({"error": f"{type(e).__name__}: {e}", "kind": "crash"})
    finally:
        conn.close()


def run(filename: str, data: bytes, use_model: bool, timeout: float | None = None) -> dict:
    """{"result", "reports", "tokens"} or WorkerError. Blocks: call it from a thread."""
    timeout = config.CHECK_TIMEOUT if timeout is None else timeout
    parent, child = _CTX.Pipe(duplex=False)
    proc = _CTX.Process(target=_child, args=(child, filename, data, use_model), daemon=True)
    proc.start()
    child.close()
    try:
        if not parent.poll(timeout):
            raise WorkerError("Проверка заняла слишком много времени. Попробуйте файл покороче.", "crash")
        out = parent.recv()
    except EOFError:
        # the child died without an answer: out of memory most likely
        raise WorkerError("Не получилось проверить файл, попробуйте другой.", "crash") from None
    finally:
        if proc.is_alive():
            proc.kill()
        proc.join(5)
        parent.close()
    if "error" in out:
        if out["kind"] == "crash":
            log.error("check of %s failed in the child: %s", filename, out["error"])
            raise WorkerError("Не получилось проверить файл, попробуйте другой.", "crash")
        raise WorkerError(out["error"], out["kind"])
    return out
