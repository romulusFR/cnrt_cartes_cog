async function addViz(url, containerId) {
    const spec = await fetch(url)
        .then((res) => res.json())
        .catch(console.error);

    const view = new vega.View(vega.parse(spec), {
        renderer: "svg",
        container: containerId,
        hover: false,
        // logLevel : vega.Debug
    });
    return view.runAsync();
}

// addViz("specs/vega-sunburst.json", "#view-sunburst");
// addViz("specs/vega-tree.json", "#view-tree");
// addViz("specs/vega-radial.json", "#view-radial");
// addViz("specs/vega-treemap.json", "#view-treemap");

console.info(`vega.version = ${vega.version}`);
console.info(`vegaLite.version = ${vegaLite.version}`);
console.info(`vegaEmbed.version = ${vegaEmbed.version}`);

vegaOptions = {
    renderer: "svg",
    actions: { export: true, source: true, compiled: false, editor: false },
    // theme: "quartz",
};

vegaEmbed("#view-sunburst", "specs/vega-sunburst.json", vegaOptions);
vegaEmbed("#view-tree", "specs/vega-tree.json", vegaOptions);
vegaEmbed("#view-radial", "specs/vega-radial.json", vegaOptions);
vegaEmbed("#view-treemap", "specs/vega-treemap.json", vegaOptions);
vegaEmbed("#view-circle", "specs/vega-circle.json", vegaOptions);
vegaEmbed("#view-wordcloud", "specs/vega-wordcloud.json", vegaOptions);
vegaEmbed("#view-hist", "specs/vega-lite-hist.json", vegaOptions);
vegaEmbed("#view-lite-heatmap", "specs/vega-lite-heatmap.json", vegaOptions);