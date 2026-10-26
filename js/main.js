document.documentElement.classList.add("js");

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
  background: "#fffdf7",
  font: "Figtree",
  view: { stroke: null },
  axis: {
    labelFontSize: 12, labelColor: "#3d4650",
    titleFontSize: 12, titleFontWeight: 600, titleColor: "#1b2430",
    domainColor: "#b9c0c4", tickColor: "#b9c0c4", gridColor: "#e6eaea",
  },
  legend: { labelFontSize: 12, labelColor: "#3d4650", titleFontSize: 12, titleFontWeight: 600, titleColor: "#1b2430" },
  header: { labelFont: "Figtree", labelColor: "#20242b" },
  text: { font: "Figtree" },
};

for (const id of charts) {
  const controls = document.getElementById(`ctl-${id}`);
  const options = { actions: false, config: theme };
  if (controls) options.bind = controls;
  vegaEmbed(`#${id}`, `specs/${id}.vg.json`, options)
    .then(() => controls && addControlIcons(controls))
    .catch(console.error);
}

// Put an icon from the page's set in front of each control label:
// sort arrows for "Sort ...", a magnifier for search boxes, a funnel for other dropdowns.
function addControlIcons(controls) {
  for (const bind of controls.querySelectorAll(".vega-bind")) {
    const name = bind.querySelector(".vega-bind-name");
    if (!name || name.querySelector("svg")) continue;
    const icon = bind.querySelector('input[type="search"]') ? "search"
      : name.textContent.trim().startsWith("Sort") ? "sort" : "filter";
    name.insertAdjacentHTML("afterbegin",
      `<svg class="control-icon" aria-hidden="true"><use href="#i-${icon}"/></svg>`);
  }
}

// The little trolley on the aisle bar rolls along as you scroll down the page.
const nav = document.querySelector(".aisles-nav");
function trackScroll() {
  const max = document.documentElement.scrollHeight - innerHeight;
  nav.style.setProperty("--p", max > 0 ? Math.min(scrollY / max, 1) : 0);
}
addEventListener("scroll", trackScroll, { passive: true });
trackScroll();

// Highlight the aisle you are in.
const links = new Map([...nav.querySelectorAll("a")].map(a => [a.hash.slice(1), a]));
const aisleObserver = new IntersectionObserver(entries => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    links.forEach(a => a.classList.remove("is-here"));
    links.get(e.target.id)?.classList.add("is-here");
  }
}, { rootMargin: "-45% 0px -50% 0px" });
document.querySelectorAll("main section[id]").forEach(s => aisleObserver.observe(s));

// The checkout receipt prints once, when its top reaches the lower part of the screen.
// Checked on scroll (and once on load), so it can never stay hidden.
const receipt = document.querySelector(".receipt");
function printReceipt() {
  if (receipt.classList.contains("is-printed")) return;
  if (receipt.getBoundingClientRect().top < innerHeight * 0.85) receipt.classList.add("is-printed");
}
addEventListener("scroll", printReceipt, { passive: true });
printReceipt();
