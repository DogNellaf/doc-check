import hashlib
import shutil

import numpy as np
import pytest

from app import config
from app.company import load
from app.engine.embed import DIM
from app.engine.lexical import stems

HAS_MODEL = (config.MODEL_DIR / "onnx" / "model_quantized.onnx").exists()
HAS_TESSERACT = shutil.which("tesseract") is not None


class FakeEmbedder:
    """Bag of word stems hashed into 384 numbers: similar words, similar vectors, no model."""

    def embed(self, texts, kind):
        out = np.zeros((len(texts), DIM), dtype=np.float32)
        for i, t in enumerate(texts):
            for s in stems(t):
                out[i, int(hashlib.md5(s[:4].encode()).hexdigest(), 16) % DIM] += 1
            out[i, 0] += 0.5  # keeps every vector non-zero
        return out / np.linalg.norm(out, axis=1, keepdims=True)


@pytest.fixture
def fake_thresholds(monkeypatch):
    # FakeEmbedder similarities are lower than e5 ones; the real thresholds are checked in test_smoke
    monkeypatch.setattr(config, "CLAUSE_MIN_DENSE", 0.5)
    monkeypatch.setattr(config, "ITEM_MIN_DENSE", 0.5)


@pytest.fixture(scope="session")
def company():
    return load(config.COMPANY_DIR)


@pytest.fixture(scope="session")
def e5():
    if not HAS_MODEL:
        pytest.skip("no model: python scripts/download_model.py")
    from app.engine.embed import E5Embedder

    return E5Embedder(config.MODEL_DIR)


def example(name: str) -> bytes:
    return (config.EXAMPLES_DIR / name).read_bytes()
