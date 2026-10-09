// Each chart's Vega-Lite spec lives in specs/<id>.vg.json and renders into <div id="<id>">.
const charts = ["imports_choropleth", "imports_flow", "supermarkets_dotmap"];

const embedOptions = {
  actions: false,
  config: {
    font: "DM Sans",
    axis: { labelFontSize: 12, titleFontSize: 12, titleFontWeight: 500 },
    legend: { labelFontSize: 12, titleFontSize: 12, titleFontWeight: 500 },
  },
};

for (const id of charts) {
  vegaEmbed(`#${id}`, `specs/${id}.vg.json`, embedOptions).catch(console.error);
}
