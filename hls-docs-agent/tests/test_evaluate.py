import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.evaluate import evaluate


def test_retrieval_quality_does_not_regress():
    result = evaluate(k=3)
    direct = result["stats"]["direct"]
    overall = result["stats"]["all"]

    # Guard rails: if chunking or embedding changes make retrieval worse,
    # this test fails. Thresholds sit just below the measured baseline.
    assert direct["r1"] / direct["n"] >= 0.8
    assert overall["rk"] / overall["n"] >= 0.9
