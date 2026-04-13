#!/usr/bin/env python3
"""
sync.py — Pulls the latest Terminology data from Notion and regenerates terms.json.

Two ways to trigger a sync:

1. ASK CLAUDE (easiest) — say "sync the glossary" in Claude Code. Claude reads the
   Notion DB via its built-in connector, regenerates terms.json, and pushes to GitHub.
   No setup needed.

2. RUN THIS SCRIPT — useful if you want to sync independently of Claude.
   Setup (one time):
     a) Create a Notion integration at https://www.notion.so/my-integrations
        (any name; "internal" type; copy the secret token)
     b) Open the Terminology DB in Notion → ... menu → Connections → add your
        integration so it has read access
     c) export NOTION_TOKEN="secret_xxxxxxxxxx"
     d) pip install -r requirements.txt
   Run:
     python sync.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("Missing dependency. Run:  pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)


# ============================================================
# CONFIGURATION
# Update these two if Notion is moved/restructured.
# ============================================================
DATABASE_ID = "940438d6-b6b2-4518-b128-71b28fb8715e"  # Terminology database

# Categories must match the SELECT options in the Notion DB schema.
# Order here = order of tabs on the page.
CATEGORIES = [
    "Disease & Anatomy",
    "Biomarkers & Lab",
    "Imaging Modalities",
    "Quantitative Imaging Metrics",
    "Diagnostic Radiotracers",
    "Therapy & Theranostics",
    "Response Assessment",
    "Reading & Workflow",
    "Nucs AI Products",
    "Clinical Trials",
    "Regulatory",
    "QMS Documentation",
    "Stakeholders & PR",
    "Conferences",
    "Journals",
    "Competitors / Industry",
]

NOTION_VERSION = "2022-06-28"
OUTPUT_FILE = Path(__file__).parent / "terms.json"


def get_token() -> str:
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        print("ERROR: NOTION_TOKEN environment variable not set.", file=sys.stderr)
        print("See setup instructions at the top of this file.", file=sys.stderr)
        sys.exit(1)
    return token


def fetch_all_pages(token: str) -> list[dict]:
    """Query the Notion database, paginating through all pages."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    pages = []
    payload = {"page_size": 100}
    while True:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return pages


def extract_text(prop: dict) -> str:
    """Extract plain text from a Notion title or rich_text property."""
    if not prop:
        return ""
    items = prop.get("title") or prop.get("rich_text") or []
    return "".join(i.get("plain_text", "") for i in items).strip()


def parse_synonyms(raw: str) -> list[str]:
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def to_term(page: dict) -> dict | None:
    props = page.get("properties", {})
    term = extract_text(props.get("Term"))
    definition = extract_text(props.get("Definition"))
    category_prop = props.get("Category", {}).get("select") or {}
    category = category_prop.get("name", "")
    synonyms_raw = extract_text(props.get("Synonyms"))

    if not term:
        return None  # skip empty rows

    return {
        "term": term,
        "def": definition,
        "category": category,
        "synonyms": parse_synonyms(synonyms_raw),
    }


def main():
    token = get_token()
    print(f"Fetching pages from Notion DB {DATABASE_ID}...")
    pages = fetch_all_pages(token)
    print(f"  → {len(pages)} pages fetched")

    terms = [t for t in (to_term(p) for p in pages) if t]
    print(f"  → {len(terms)} valid terms")

    # Sort by category order (matching CATEGORIES list), then by term name within each
    cat_order = {c: i for i, c in enumerate(CATEGORIES)}
    terms.sort(key=lambda t: (cat_order.get(t["category"], 999), t["term"].lower()))

    # Warn about any unrecognized categories
    used_cats = {t["category"] for t in terms}
    unknown = used_cats - set(CATEGORIES)
    if unknown:
        print(f"  ⚠ Unrecognized categories in Notion: {unknown}")
        print(f"    Add them to CATEGORIES in sync.py to control tab order.")

    output = {
        "version": "1",
        "lastSynced": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": f"Notion DB: Terminology (https://www.notion.so/{DATABASE_ID.replace('-', '')})",
        "categories": CATEGORIES,
        "terms": terms,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"  → wrote {OUTPUT_FILE}")
    print("Done. Commit and push to deploy:")
    print('  git commit -am "Sync glossary" && git push')


if __name__ == "__main__":
    main()
