"""Inspect a wheel without installing or extracting it."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from email.parser import Parser
from pathlib import Path


def inspect_wheel(path: Path) -> dict[str, object]:
    wheel = path.resolve()
    with zipfile.ZipFile(wheel) as archive:
        names = sorted(archive.namelist())
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
    return {
        "path": str(wheel),
        "size_bytes": wheel.stat().st_size,
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "name": metadata["Name"],
        "version": metadata["Version"],
        "requires_python": metadata["Requires-Python"],
        "requires_dist": metadata.get_all("Requires-Dist", []),
        "files": names,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", nargs="?", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    wheel = arguments.wheel
    if wheel is None:
        wheels = sorted((Path(__file__).resolve().parents[1] / "dist").glob("*.whl"))
        if len(wheels) != 1:
            parser.error("provide a wheel or leave exactly one wheel in dist")
        wheel = wheels[0]
    rendered = json.dumps(inspect_wheel(wheel), indent=2, ensure_ascii=False)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
