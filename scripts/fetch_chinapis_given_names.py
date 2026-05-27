"""Fetch ChinAPIs given-name character frequency data.

The upstream dataset is distributed inside the CRAN R package ChinAPIs as
`given_name_df.rda`. This script downloads the package and converts that R data
file to CSV so the rest of the project can consume it without requiring R.
"""
from __future__ import annotations

import argparse
import io
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "0.1.1"
DEFAULT_OUT = ROOT / "data" / "raw" / "chinapis_given_name_df.csv"


def download_package(version: str) -> bytes:
    url = f"https://cran.r-project.org/src/contrib/ChinAPIs_{version}.tar.gz"
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def extract_rda(package_bytes: bytes) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(package_bytes), mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith("data/given_name_df.rda"):
                file = tar.extractfile(member)
                if file is None:
                    break
                return file.read()
    raise FileNotFoundError("data/given_name_df.rda not found in ChinAPIs package")


def rda_to_csv(rda_bytes: bytes, out_path: Path) -> int:
    try:
        import pandas as pd  # type: ignore
        import rdata  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Missing Python dependencies for RData conversion. "
            "Install them with: pip install rdata pandas"
        ) from exc

    parsed = rdata.parser.parse_data(rda_bytes)
    converted = rdata.conversion.convert(parsed)
    df = converted["given_name_df"]
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")
    return len(df)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch ChinAPIs given_name_df as CSV")
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    package = download_package(args.version)
    rda = extract_rda(package)
    count = rda_to_csv(rda, args.out)
    print(f"Wrote {count} rows -> {args.out}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise
