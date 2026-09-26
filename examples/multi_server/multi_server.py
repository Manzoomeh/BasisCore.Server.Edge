"""Launch two Edge processes (A on 9187, B on 9188)."""
import sys
from pathlib import Path

from bclib import edge

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable

if __name__ == "__main__":
    print("Starting multi_server (A:9187, B:9188)...")
    edge.from_list(
        {
            "rest-a": [PY, str(ROOT / "examples/multi_server/simple_rest_a.py")],
            "rest-b": [PY, str(ROOT / "examples/multi_server/simple_rest_b.py")],
        }
    )
