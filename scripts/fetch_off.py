"""Download Australian products with complete nutrition facts from Open Food Facts.

Keeps products with an Australian GS1 barcode prefix (93), complete nutrition
facts and complete categories (8,881 products in Oct 2026). Uses the Open Food
Facts search API (search.openfoodfacts.org), which returns at most 10,000 matches. Writes one JSON Lines file per page to raw/off/ so a failed
run can resume. Source: https://world.openfoodfacts.org (ODbL licence).
"""
import json
import pathlib
import time
import urllib.parse
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent.parent / "raw" / "off"
QUERY = ('code:93* AND countries_tags:"en:australia"'
         ' AND states_tags:"en:nutrition-facts-completed"'
         ' AND states_tags:"en:categories-completed"')
FIELDS = ",".join([
    "code", "product_name", "brands", "categories_tags", "nutriscore_grade",
    "nova_group", "origins_tags", "manufacturing_places", "stores_tags",
    "additives_n", "nutriments", "unique_scans_n",
])
PAGE_SIZE = 100
KEEP_NUTRIENTS = ["energy-kcal_100g", "sugars_100g", "salt_100g", "sodium_100g",
                  "saturated-fat_100g", "fat_100g", "proteins_100g", "fiber_100g"]


def fetch(page):
    qs = urllib.parse.urlencode({"q": QUERY, "fields": FIELDS,
                                 "page_size": PAGE_SIZE, "page": page,
                                 "sort_by": "-unique_scans_n"})
    req = urllib.request.Request("https://search.openfoodfacts.org/search?" + qs,
                                 headers={"User-Agent": "FIT3179-student-project/1.0"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # rate limit or timeout: back off and retry
            print(f"page {page} attempt {attempt}: {e}", flush=True)
            time.sleep(20 * (attempt + 1))
    raise RuntimeError(f"page {page} failed")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    page, last = 1, 10_000 // PAGE_SIZE
    while page <= last:
        path = OUT / f"page_{page:03d}.jsonl"
        if not path.exists():
            hits = fetch(page)["hits"]
            if not hits:
                break
            with path.open("w", encoding="utf-8") as f:
                for p in hits:
                    n = p.get("nutriments") or {}
                    p["nutriments"] = {k: n[k] for k in KEEP_NUTRIENTS if k in n}
                    f.write(json.dumps(p, ensure_ascii=False) + "\n")
            print(f"page {page}: {len(hits)}", flush=True)
            time.sleep(1)
        page += 1


if __name__ == "__main__":
    main()
