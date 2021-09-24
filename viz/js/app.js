// "https://vega.github.io/vega/examples/bar-chart.vg.json"

const url = "specs/vega-radial.json";
fetch(url)
    .then((res) => res.json())
    .then((spec) => render(spec))
    .catch((err) => console.error(err));

function render(spec) {
    const view = new vega.View(vega.parse(spec), {
        renderer: "svg", // renderer (canvas or svg)
        container: "#tree-view", // parent DOM container
        hover: false, // enable hover processing
    });
    return view.runAsync();
}
