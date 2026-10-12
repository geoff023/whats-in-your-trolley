// Each chart's spec lives in specs/<id>.vg.json and renders into <div id="<id>">.
// If the card has a <div id="ctl-<id>">, the chart's dropdowns and search box go there,
// so every control sits in the same place: between the note and the chart.
const charts = [
  "imports_choropleth", "imports_types_bar", "imports_flow",
  "supermarkets_dotmap", "chains_by_state",
  "prices_line", "prices_symbol_map", "prices_heatmap", "prices_bump",
  "nutrients_explorer", "nova_waffle",
  "brand_treemap", "brand_nutriscore",
];

// Shared theme: one typeface and the page's colours in every chart.
const theme = {
  background: "#ffffff",
  font: "Archivo",
  view: { stroke: null },
  axis: {
    labelFontSize: 12, labelColor: "#3d4650",
    titleFontSize: 12, titleFontWeight: 600, titleColor: "#1b2430",
    domainColor: "#b9c0c4", tickColor: "#b9c0c4", gridColor: "#e6eaea",
  },
  legend: { labelFontSize: 12, labelColor: "#3d4650", titleFontSize: 12, titleFontWeight: 600, titleColor: "#1b2430" },
  header: { labelFont: "Archivo", labelColor: "#1b2430" },
  text: { font: "Archivo" },
};

for (const id of charts) {
  const controls = document.getElementById(`ctl-${id}`);
  const options = { actions: false, config: theme };
  if (controls) options.bind = controls;
  vegaEmbed(`#${id}`, `specs/${id}.vg.json`, options).catch(console.error);
}
