"""Turn the raw downloads in raw/ into the small files in data/ used by the charts.

Run after fetch_off.py and the curl downloads listed in README.md:
    python -X utf8 scripts/process.py
"""
import csv
import glob
import json
import pathlib
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, DATA = ROOT / "raw", ROOT / "data"

# First matching category tag decides the aisle, so specific tags come first.
AISLES = [
    ("Muesli & protein bars", ["en:cereal-bars", "en:protein-bars"]),
    ("Confectionery", ["en:confectioneries", "en:chocolates"]),
    ("Biscuits & cakes", ["en:biscuits-and-cakes"]),
    ("Chips & salty snacks", ["en:salty-snacks"]),
    ("Breakfast cereals", ["en:breakfast-cereals"]),
    ("Yoghurt", ["en:yogurts"]),
    ("Cheese", ["en:cheeses"]),
    ("Milk & alternatives", ["en:milks", "en:dairy-substitutes", "en:plant-based-milk-alternatives"]),
    ("Ice cream & desserts", ["en:frozen-desserts", "en:desserts"]),
    ("Spreads", ["en:spreads"]),
    ("Sauces & condiments", ["en:sauces", "en:condiments"]),
    ("Bread", ["en:breads"]),
    ("Meat & seafood", ["en:meats-and-their-products", "en:seafood"]),
    ("Ready meals", ["en:meals"]),
    ("Soft drinks & juice", ["en:sweetened-beverages", "en:juices-and-nectars", "en:sodas",
                             "en:fruit-based-beverages"]),
    ("Pasta, rice & grains", ["en:pastas", "en:rices", "en:cereal-grains", "en:cereals-and-their-products"]),
    ("Fruit, veg & legumes", ["en:fruits-and-vegetables-based-foods", "en:legumes-and-their-products",
                              "en:nuts-and-their-products"]),
]
SKIP = {"en:alcoholic-beverages", "en:dietary-supplements", "en:baby-foods"}
HOUSE_BRANDS = ("woolworths", "coles", "macro", "aldi", "black & gold", "community co",
                "essentials", "homebrand", "simply", "smart buy", "farmers market")


def first(value):
    """OFF brands come as a comma string or a list; return the first brand."""
    if isinstance(value, list):
        value = ",".join(value)
    return (value or "").split(",")[0].strip()


def num(v, nd=2):
    """Per-100 g value, or blank. Nothing can weigh more than 100 g per 100 g, so larger
    values are data-entry errors (often milligrams typed into a grams field)."""
    if v is None or not 0 <= float(v) <= 100:
        return ""
    return round(float(v), nd)


def products():
    rows = []
    for f in sorted(glob.glob(str(RAW / "off" / "*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            p = json.loads(line)
            tags = p.get("categories_tags") or []
            if SKIP & set(tags):
                continue
            aisle = next((name for name, keys in AISLES if any(k in tags for k in keys)), None)
            if not aisle:
                continue
            brand = first(p.get("brands"))
            low = brand.lower()
            n = p["nutriments"]
            grade = p.get("nutriscore_grade")
            rows.append({
                "name": (p.get("product_name") or "").strip()[:60],
                "brand": brand,
                "brand_type": "Unknown" if not brand else
                              "Supermarket own brand" if low.startswith(HOUSE_BRANDS) else "Name brand",
                "aisle": aisle,
                "nutriscore": grade.upper() if grade in ("a", "b", "c", "d", "e") else "",
                "nova": p.get("nova_group") or "",
                "kcal": round(float(n["energy-kcal_100g"])) if 0 <= float(n.get("energy-kcal_100g", -1)) <= 900 else "",
                "sugar": num(n.get("sugars_100g"), 1),
                "salt": num(n.get("salt_100g"), 2),
                "satfat": num(n.get("saturated-fat_100g"), 1),
                "protein": num(n.get("proteins_100g"), 1),
                "fibre": num(n.get("fiber_100g"), 1),
                "additives": p.get("additives_n", ""),
                "scans": p.get("unique_scans_n") or 0,
            })
    # One spelling per brand: "ARNOTT'S", "arnotts" and "Arnott's" all become the most common
    # mixed-case spelling ("Arnott's").
    key = lambda b: "".join(ch for ch in b.lower() if ch.isalnum())
    spellings = defaultdict(Counter)
    for r in rows:
        spellings[key(r["brand"])][r["brand"]] += 1
    best = {k: max(c, key=lambda b: (b != b.lower() and b != b.upper(), c[b])) for k, c in spellings.items()}
    for r in rows:
        r["brand"] = best[key(r["brand"])]
    write("products.csv", rows)
    print("products", len(rows), Counter(r["aisle"] for r in rows).most_common())
    nova_waffle(rows)
    brand_tree(rows)


def nova_waffle(rows):
    """100 cells per aisle for the waffle chart: each cell is 1% of that aisle's products
    with a known NOVA group. Largest-remainder rounding keeps each aisle at exactly 100."""
    out = []
    for aisle in sorted({r["aisle"] for r in rows}):
        groups = Counter(r["nova"] for r in rows if r["aisle"] == aisle and r["nova"])
        total = sum(groups.values())
        exact = {g: 100 * c / total for g, c in groups.items()}
        cells = {g: int(v) for g, v in exact.items()}
        for g in sorted(exact, key=lambda g: exact[g] - cells[g], reverse=True)[:100 - sum(cells.values())]:
            cells[g] += 1
        share4 = cells.get(4, 0)
        i = 0
        for g in (4, 3, 2, 1):
            for _ in range(cells.get(g, 0)):
                out.append({"aisle": aisle, "cell": i, "col": i % 10, "row": i // 10, "nova": g,
                            "ultra_pct": share4, "n": total})
                i += 1
    write("nova_waffle.csv", out)


def brand_tree(rows):
    """Products per aisle, split into own brands and name brands. The biggest brands keep their
    name (top 3 own, top 4 name); the rest are pooled so the treemap stays readable."""
    out = []
    for aisle in sorted({r["aisle"] for r in rows}):
        for kind, keep, other in (("Supermarket own brand", 3, "Other own brands"),
                                  ("Name brand", 4, "Other name brands")):
            counts = Counter(r["brand"] for r in rows
                             if r["aisle"] == aisle and r["brand_type"] == kind)
            top = counts.most_common(keep)
            for brand, n in top:
                out.append({"aisle": aisle, "brand": brand, "shade": kind, "products": n})
            rest = sum(counts.values()) - sum(n for _, n in top)
            if rest:
                out.append({"aisle": aisle, "brand": other, "shade": other, "products": rest})
    write("brand_tree.csv", out)


CITIES = {  # ABS CPI region code: capital city, state, lon, lat
    "1": ("Sydney", "NSW", 151.21, -33.87), "2": ("Melbourne", "VIC", 144.96, -37.81),
    "3": ("Brisbane", "QLD", 153.03, -27.47), "4": ("Adelaide", "SA", 138.60, -34.93),
    "5": ("Perth", "WA", 115.86, -31.95), "6": ("Hobart", "TAS", 147.33, -42.88),
    "7": ("Darwin", "NT", 130.84, -12.46), "8": ("Canberra", "ACT", 149.13, -35.28),
}
CPI_GROUPS = {"30001": "Dairy", "30002": "Bread & cereals", "30003": "Meat & seafood",
              "114120": "Fruit & veg"}


def cpi():
    rows = []
    for r in csv.DictReader(open(RAW / "abs_cpi_food_v2_monthly.csv", encoding="utf-8")):
        if r["INDEX"] in CPI_GROUPS and (r["REGION"] in CITIES or r["REGION"] == "50"):
            city, state, lon, lat = CITIES.get(r["REGION"], ("Australia", "AUS", "", ""))
            rows.append({"month": r["TIME_PERIOD"], "city": city, "state": state,
                         "lon": lon, "lat": lat, "group": CPI_GROUPS[r["INDEX"]],
                         "index": float(r["OBS_VALUE"])})
    rows.sort(key=lambda r: (r["group"], r["city"], r["month"]))
    # Re-base every series to September 2017 = 100, the first month all series share,
    # so the charts read as "% change since 2017".
    start = {(r["group"], r["city"]): r["index"] for r in rows if r["month"] == "2017-09"}
    for r in rows:
        r["since2017"] = round(100 * r["index"] / start[(r["group"], r["city"])], 2)
    write("cpi_food_monthly.csv", rows)
    print("cpi", len(rows), min(r["month"] for r in rows), max(r["month"] for r in rows))


HS = {"02": "Meat", "03": "Fish & seafood", "04": "Dairy, eggs & honey", "07": "Vegetables",
      "08": "Fruit & nuts", "09": "Coffee, tea & spices", "10": "Cereals", "15": "Oils & fats",
      "16": "Preserved meat & fish", "17": "Sugar & lollies", "18": "Cocoa & chocolate",
      "19": "Bakery, pasta & cereal foods", "20": "Preserved fruit & veg",
      "21": "Sauces & other foods", "22": "Drinks"}


def imports():
    partners = {p["PartnerCode"]: p for p in json.load(open(RAW / "comtrade" / "partners.json",
                                                             encoding="utf-8"))["results"]}
    ne = json.load(open(RAW / "ne_countries.geojson", encoding="utf-8"))["features"]
    # Natural Earth codes a few countries with -99 in ISO_A3, so key on ISO_A3_EH.
    centre = {f["properties"]["ISO_A3_EH"]: (f["properties"]["LABEL_X"], f["properties"]["LABEL_Y"])
              for f in ne}
    centre.update({"SGP": (103.82, 1.35), "HKG": (114.17, 22.32)})  # too small for 1:110m
    # Comtrade codes differ from ISO for some countries (USA 842 vs 840), so take ISO numeric
    # from Natural Earth; it matches the ids in the world-110m TopoJSON used by the maps.
    iso_n3 = {f["properties"]["ISO_A3_EH"]: int(f["properties"]["ISO_N3_EH"]) for f in ne
              if f["properties"]["ISO_N3_EH"] not in ("-99", None)}
    by_chapter, by_country = [], defaultdict(float)
    for code, label in HS.items():
        for r in json.load(open(RAW / "comtrade" / f"hs{code}.json"))["data"]:
            p = partners.get(r["partnerCode"])
            if not p or r["partnerCode"] == 0 or p.get("isGroup"):
                continue
            iso3, name = p["PartnerCodeIsoAlpha3"], p["PartnerDesc"]
            if r["partnerCode"] == 490:  # Comtrade reports Taiwan as "Other Asia, nes"
                iso3, name = "TWN", "Taiwan"
            by_chapter.append({"iso3": iso3, "country": name, "chapter": label,
                               "usd_m": round(r["primaryValue"] / 1e6, 2)})
            by_country[iso3] += r["primaryValue"]
    write("imports_by_chapter_2025.csv", by_chapter)
    names = {r["iso3"]: r["country"] for r in by_chapter}
    countries = [{"iso3": k, "iso_n3": iso_n3.get(k, ""), "country": names[k],
                  "usd_m": round(v / 1e6, 1),
                  "lon": centre.get(k, ("", ""))[0], "lat": centre.get(k, ("", ""))[1]}
                 for k, v in sorted(by_country.items(), key=lambda kv: -kv[1])]
    write("imports_by_country_2025.csv", countries)
    print("imports", len(countries), "countries; top", countries[:5])
    print("top 20 without centroid", [c["country"] for c in countries[:20] if c["lon"] == ""])
    print("top 40 without iso_n3", [c["country"] for c in countries[:40] if c["iso_n3"] == ""])


def inside(lon, lat, ring):
    """Ray casting point-in-polygon test on a lon/lat ring."""
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


STATE_ABBR = {"New South Wales": "NSW", "Victoria": "VIC", "Queensland": "QLD", "South Australia": "SA",
              "Western Australia": "WA", "Tasmania": "TAS", "Northern Territory": "NT",
              "Australian Capital Territory": "ACT"}
_SHAPES = []


def state_of(lon, lat):
    if not _SHAPES:
        for f in json.load(open(RAW / "au_states.geojson", encoding="utf-8"))["features"]:
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in polys:
                xs, ys = [c[0] for c in poly[0]], [c[1] for c in poly[0]]
                _SHAPES.append((STATE_ABBR[f["properties"]["STATE_NAME"]], poly,
                                (min(xs), min(ys), max(xs), max(ys))))
    for abbr, poly, (x0, y0, x1, y1) in _SHAPES:
        # Inside the outer ring and not inside a hole (NSW has a hole where the ACT is).
        if (x0 <= lon <= x1 and y0 <= lat <= y1 and inside(lon, lat, poly[0])
                and not any(inside(lon, lat, hole) for hole in poly[1:])):
            return abbr
    # ponytail: coastal stores just outside the simplified outline go to the nearest bbox.
    return min(_SHAPES, key=lambda s: max(s[2][0] - lon, lon - s[2][2], s[2][1] - lat, lat - s[2][3]))[0]


def stores():
    els = json.load(open(RAW / "osm_supermarkets.json", encoding="utf-8"))["elements"]
    rows = []
    for e in els:
        lat = e.get("lat") or e.get("center", {}).get("lat")
        lon = e.get("lon") or e.get("center", {}).get("lon")
        # The download bbox also catches PNG, Timor and Indonesian islands.
        if lat is None or lat > -10.4 or (lon < 129 and lat > -11.5):
            continue
        b = (e.get("tags", {}).get("brand") or "").lower()
        chain = ("Woolworths" if b.startswith("woolworths") else "Coles" if b.startswith("coles")
                 else "Aldi" if b == "aldi" else "IGA" if "iga" in b else "Other")
        rows.append({"chain": chain, "state": state_of(lon, lat), "lon": round(lon, 3), "lat": round(lat, 3)})
    write("supermarkets.csv", rows)
    print("stores", len(rows), Counter(r["chain"] for r in rows), Counter(r["state"] for r in rows))


def write(name, rows):
    with open(DATA / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def clockwise(ring):
    """Shoelace sum over lon/lat; negative means clockwise."""
    return sum((x2 - x1) * (y2 + y1) for (x1, y1), (x2, y2) in zip(ring, ring[1:])) > 0


def states():
    """Vega (d3-geo) needs clockwise outer rings and anticlockwise holes. The source file mixes
    both, so some states filled the whole globe except themselves."""
    gj = json.load(open(RAW / "au_states.geojson", encoding="utf-8"))
    for f in gj["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for i, ring in enumerate(poly):
                if clockwise(ring) != (i == 0):
                    ring.reverse()
    with open(DATA / "au_states.geojson", "w", encoding="utf-8") as f:
        json.dump(gj, f, separators=(",", ":"))


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    products()
    cpi()
    imports()
    stores()
    states()
