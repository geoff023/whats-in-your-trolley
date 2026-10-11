// Each chart's spec lives in specs/<id>.vg.json and renders into <div id="<id>">.
const charts = [
  "imports_choropleth", "imports_types_bar", "imports_flow",
  "supermarkets_dotmap", "chains_by_state",
  "prices_line", "prices_symbol_map", "prices_heatmap", "prices_bump",
  "nutrient_heatmap", "nutrient_strip", "nova_waffle",
  "brand_treemap", "brand_nutriscore",
];

// Shared theme so every chart matches the page: one font, card background, muted axes.
const theme = {
  background: "#fffdf8",
  font: "DM Sans",
  view: { stroke: null },
  axis: {
    labelFontSize: 12, labelColor: "#3b4248",
    titleFontSize: 12, titleFontWeight: 500, titleColor: "#1d2327",
    domainColor: "#b8b2a7", tickColor: "#b8b2a7", gridColor: "#ece6da",
  },
  legend: { labelFontSize: 12, labelColor: "#3b4248", titleFontSize: 12, titleFontWeight: 500, titleColor: "#1d2327" },
  header: { labelFont: "DM Sans", labelColor: "#1d2327" },
  text: { font: "DM Sans" },
};

for (const id of charts) {
  vegaEmbed(`#${id}`, `specs/${id}.vg.json`, { actions: false, config: theme }).catch(console.error);
}
