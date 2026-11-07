"""Check the examples once, when the image is built: python -m app.precompute

Each example leaves <id>.json (the result as the API returns it) and its two reports in
PRECOMPUTED_DIR. The service only reads these files at start, so it starts at once, never runs
Tesseract for the scan on start and opens the examples without loading any of the heavy libraries.
"""

from __future__ import annotations

import json
import logging
import sys

from . import config, pipeline
from .company import load
from .service import EXAMPLES

log = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    company = load(config.COMPANY_DIR)
    out = config.PRECOMPUTED_DIR
    out.mkdir(parents=True, exist_ok=True)
    failed = 0
    for ex in EXAMPLES:
        path = config.EXAMPLES_DIR / ex["file"]
        try:
            result, _ = pipeline.check(company, ex["file"], path.read_bytes())
        except Exception as e:  # noqa: BLE001 - a scan without Tesseract on a dev machine
            log.warning("example %s: %s", ex["file"], e)
            failed += 1
            continue
        result["id"] = f"example-{ex['id']}"
        result["example"] = ex["id"]
        (out / f"{ex['id']}.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        for fmt, (data, name) in pipeline.reports(result, company).items():
            (out / f"{ex['id']}.{fmt}").write_bytes(data)
            (out / f"{ex['id']}.{fmt}.name").write_text(name, encoding="utf-8")
        log.info("%s: %s, %d findings", ex["id"], result["verdict"]["text"], len(result["findings"]))
    return 1 if failed and "--strict" in sys.argv else 0


if __name__ == "__main__":
    sys.exit(main())
