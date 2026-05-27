"""
从 Wikidata（QLever 镜像）拉取知名人物，落到 data/raw/wikidata_famous.jsonl。

为什么用 QLever：
- 官方 query.wikidata.org 当前在中国常常被代理/限流为 1 req/min
- QLever (https://qlever.dev) 是 Freiburg 大学的 Wikidata 公共镜像，无限流

策略：
- 按 sitelinks 分档查询，避免单次查询过大
- 拉取所有"有中文标签"的人物后，在 import 环节再用百家姓过滤为中国人
- 用 stdlib urllib 而非 requests，更稳定地穿过代理

JSONL 入 git。原始数据落盘后跑 import_famous_names.py --source wikidata 入库。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "raw" / "wikidata_famous.jsonl"

ENDPOINT = "https://qlever.dev/api/wikidata"
HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": "NameProject/0.1 (data import; contact: github.com/zhanggy000/NAME)",
}

TIERS = [
    (200, None),
    (100, 200),
    (50, 100),
    (30, 50),
    (20, 30),
    (15, 20),
    (12, 15),
    (10, 12),
    (8, 10),
]

PREFIXES = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
"""

QUERY_TEMPLATE = PREFIXES + """
SELECT ?person ?personLabel ?sitelinks ?birth ?death ?genderLabel ?occLabel ?description WHERE {{
  ?person wdt:P31 wd:Q5 ;
          wikibase:sitelinks ?sitelinks ;
          rdfs:label ?personLabel .
  FILTER(LANG(?personLabel) = "zh")
  FILTER(?sitelinks >= {lo}{hi_clause})
  OPTIONAL {{ ?person wdt:P569 ?birth . }}
  OPTIONAL {{ ?person wdt:P570 ?death . }}
  OPTIONAL {{
    ?person wdt:P21 ?genderEntity .
    ?genderEntity rdfs:label ?genderLabel .
    FILTER(LANG(?genderLabel) = "zh")
  }}
  OPTIONAL {{
    ?person wdt:P106 ?occEntity .
    ?occEntity rdfs:label ?occLabel .
    FILTER(LANG(?occLabel) = "zh")
  }}
  OPTIONAL {{
    ?person schema:description ?description .
    FILTER(LANG(?description) = "zh")
  }}
}}
ORDER BY DESC(?sitelinks)
"""


def http_get(url: str, params: dict, retries: int = 3) -> dict:
    qs = urllib.parse.urlencode(params)
    full_url = f"{url}?{qs}"
    req = urllib.request.Request(full_url, headers=HEADERS)
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_err = exc
            sleep_s = 5 * (attempt + 1)
            print(f"  HTTP 第 {attempt+1} 次失败：{exc}，{sleep_s}s 后重试", file=sys.stderr)
            time.sleep(sleep_s)
    raise RuntimeError(f"HTTP 请求失败：{last_err}")


def run_query(lo: int, hi: int | None) -> list[dict]:
    hi_clause = f" && ?sitelinks < {hi}" if hi else ""
    query = QUERY_TEMPLATE.format(lo=lo, hi_clause=hi_clause)
    data = http_get(ENDPOINT, {"query": query})
    return data.get("results", {}).get("bindings", [])


def extract(binding: dict) -> dict | None:
    label = binding.get("personLabel", {}).get("value")
    if not label or not any("一" <= c <= "鿿" for c in label):
        return None
    qid = binding["person"]["value"].rsplit("/", 1)[-1]
    return {
        "qid": qid,
        "label_zh": label,
        "sitelinks": int(binding["sitelinks"]["value"]),
        "birth": binding.get("birth", {}).get("value"),
        "death": binding.get("death", {}).get("value"),
        "gender_label": binding.get("genderLabel", {}).get("value"),
        "occupation_label": binding.get("occLabel", {}).get("value"),
        "description_zh": binding.get("description", {}).get("value"),
    }


def fetch(min_sitelinks: int, max_records: int, out_path: Path) -> int:
    seen: dict[str, dict] = {}
    out_path.parent.mkdir(parents=True, exist_ok=True)

    for lo, hi in TIERS:
        if hi is not None and hi <= min_sitelinks:
            continue
        if lo < min_sitelinks:
            lo = min_sitelinks
        print(f"→ 拉取 sitelinks [{lo}-{hi or '∞'}] ...", file=sys.stderr)
        try:
            bindings = run_query(lo, hi)
        except RuntimeError as e:
            print(f"  跳过该档：{e}", file=sys.stderr)
            continue

        added = 0
        for b in bindings:
            row = extract(b)
            if not row:
                continue
            existing = seen.get(row["qid"])
            if existing:
                if row["occupation_label"]:
                    occs = set(filter(None, [
                        existing.get("occupation_label"), row["occupation_label"]
                    ]))
                    existing["occupation_label"] = " / ".join(sorted(occs))
                continue
            seen[row["qid"]] = row
            added += 1

        print(f"  新增 {added} 条，累计 {len(seen)}", file=sys.stderr)
        if len(seen) >= max_records:
            print(f"  达到上限 {max_records}，停止", file=sys.stderr)
            break
        time.sleep(1)

    rows = sorted(seen.values(), key=lambda r: -r["sitelinks"])[:max_records]
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="从 Wikidata QLever 镜像拉取人物")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--min-sitelinks", type=int, default=8)
    parser.add_argument("--max-records", type=int, default=15000)
    args = parser.parse_args()

    count = fetch(args.min_sitelinks, args.max_records, args.out)
    print(f"已写入 {count} 条 → {args.out}")


if __name__ == "__main__":
    main()
