async function addViz(url, containerId) {
    const spec = await fetch(url)
        .then((res) => res.json())
        .catch(console.error);

    const view = new vega.View(vega.parse(spec), {
        renderer: "svg",
        container: containerId,
        hover: false,
    });
    return view.runAsync();
}

addViz("specs/vega-radial.json", "#view-radial");
addViz("specs/vega-tree.json", "#view-tree");
