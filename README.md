# What's in Your Trolley?

FIT3179 Data Visualisation 2 (Monash University, 2026). A one-page visual story about Australian supermarket products, built with Vega-Lite.

- `index.html`, `css/`, `js/main.js`: the web page
- `specs/*.vg.json`: one Vega-Lite specification per chart
- `data/`: small processed data files loaded by the charts
- `scripts/`: how the data files were made

## Rebuilding the data

Raw downloads go in `raw/` (not committed).

1. Products: `python scripts/fetch_off.py` (Open Food Facts search API).
2. Food prices: ABS Data API, dataflow `ABS,CPI,2.0.0`, key `1.30001+30002+30003+114120.10..M` saved as `raw/abs_cpi_food_v2_monthly.csv`.
3. Imports: UN Comtrade public preview API, reporter 36 (Australia), flow M, period 2025, HS chapters 02–22, saved as `raw/comtrade/hsXX.json`, plus `partnerAreas.json`.
4. Supermarkets: Overpass API, `nwr["shop"="supermarket"](-44,112,-10,154)`, saved as `raw/osm_supermarkets.json`.
5. Boundaries: `raw/au_states.geojson` from rowanhogan/australian-states; `raw/ne_countries.geojson` (Natural Earth 1:110m) for country centroids.
6. `python -X utf8 scripts/process.py` writes everything in `data/`.
