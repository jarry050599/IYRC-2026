"""Generate 300 storage QR labels, one 50 mm × 12 mm label per PDF page."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.labels import labels_pdf


def generate_labels(output: Path, codes: list[str] | None = None) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(labels_pdf(codes).getvalue())
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/slot-labels.pdf"))
    args = parser.parse_args()
    print(generate_labels(args.output))
