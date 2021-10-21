"""Wrapper pour utiliser pygraphviz avec un style custom"""

from pathlib import Path
from typing import Union
import networkx as nx
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np


# pylint: disable = too-many-locals, too-many-statements
def draw_graphviz(a_graph: nx.Graph, destination: Union[Path, str], /, **gv_args) -> None:
    """Generates dot and svg using (py)graphviz

    Parameters
    ----------
    a_graph : nx.Graph
        the graph to draw
    destination:
        the file to write. Guess format from suffix

    pyargs : dict
        parameters to send to graphviz

    Returns
    -------
    int
        graphviz (twopi) return code
    """

    # default arguments
    gv_args = {
        "algorithm": "sfdp",
        "overlap": "scale",
        "sep": -0.45,
        "K": 1,
        "fontsize": 14,
        "edge_penwidths": 1,
        "min_edge_penwidths": 0.2,
        "max_edge_penwidths": 2,
        "node_color": None,
        "min_node_size": 0.1,
        "max_node_size": 1,
    } | gv_args

    # on fait une copie car on va modifier bcp d'attribut pour avoir le graphviz
    graph = a_graph.copy()
    node_names = {w: w for w in graph}
    colormap = plt.cm.get_cmap("inferno")  # plasma

    if nx.is_weighted(graph):
        # on va interpoler les tailles des arcs proportionnel au poids
        edge_weights = nx.get_edge_attributes(graph, "weight")
        min_edge_weight = min(edge_weights.values())
        max_edge_weight = max(edge_weights.values())
        penwidth_interval = [gv_args["min_edge_penwidths"], gv_args["max_edge_penwidths"]]
        edge_penwidths = {
            e: np.interp(v, [min_edge_weight, max_edge_weight], penwidth_interval) for e, v in edge_weights.items()
        }
    else:
        edge_penwidths = {k: gv_args["edge_penwidths"] for k in graph.edges}

    # idem pour la taille des noeuds
    inch_factor = 96
    node_size_interval = [gv_args["min_node_size"], gv_args["max_node_size"]]
    # min_node_size = 10 / inch_factor
    # max_node_size = min_node_size * 4
    node_nbs = nx.get_node_attributes(graph, "weight")
    min_node_nb = min(node_nbs.values())
    max_node_nb = max(node_nbs.values())

    def compute_size(value):
        return round(np.interp(value, [min_node_nb, max_node_nb], node_size_interval), 1)

    node_gwidths = {n: compute_size(v) for n, v in node_nbs.items()}

    if isinstance(gv_args["fontsize"], int):
        node_fontsize = {n: gv_args["fontsize"] for n, v in node_gwidths.items()}
    elif gv_args["fontsize"] == "proportional":
        node_fontsize = {n: v * 32 for n, v in node_gwidths.items()}

    # graph.graph["fontsize"] = gv_args["fontsize"]
    # graph.graph["fontname"] = "Helvetica"

    graph.graph["outputorder"] = "edgesfirst"
    graph.graph["bgcolor"] = "white"
    # ici pour jouer sur le rapprochement des noeuds en mode scale
    graph.graph["sep"] = gv_args["sep"]
    # -0.4 : OK pour H2
    graph.graph["overlap"] = gv_args["overlap"]  # "false" #scale false prism
    graph.graph["K"] = gv_args["K"]

    nx.set_node_attributes(graph, values=round(gv_args["min_node_size"] * inch_factor / 5), name="penwidth")  # type: ignore
    nx.set_node_attributes(graph, values=0, name="margin")
    nx.set_node_attributes(graph, values=10, name="fontsize")
    nx.set_node_attributes(graph, values="grey30", name="fontcolor")
    nx.set_node_attributes(graph, values="circle", name="shape")
    nx.set_node_attributes(graph, values="shape", name="fixedsize")
    nx.set_node_attributes(graph, values="filled", name="style")
    nx.set_node_attributes(graph, values="white", name="color")
    nx.set_node_attributes(graph, values=node_gwidths, name="width")
    nx.set_node_attributes(graph, values="Helvetica", name="fontname")
    nx.set_node_attributes(graph, values=node_fontsize, name="fontsize")
    nx.set_node_attributes(graph, values="", name="label")
    nx.set_node_attributes(graph, values=node_names, name="xlabel")

    if gv_args["node_color"] is None:
        node_colors = {k: "blue" for k in graph}
        node_label = {k: "" for k in graph}
    else:
        color_attr = nx.get_node_attributes(graph, gv_args["node_color"])
        color_norm = colors.Normalize(vmin=min(color_attr.values()), vmax=max(color_attr.values()))
        node_colors = {k: colors.rgb2hex(colormap(color_norm(v))) for k, v in color_attr.items()}
        node_label = nx.get_node_attributes(graph, "cluster")

    nx.set_node_attributes(graph, values=node_label, name="label")
    nx.set_node_attributes(graph, values=node_colors, name="fillcolor")

    nx.set_edge_attributes(graph, values=edge_penwidths, name="penwidth")
    nx.set_edge_attributes(graph, values="darkgrey", name="color")
    nx.set_edge_attributes(graph, values=gv_args["edge_penwidths"] / 2, name="arrowsize")  # type: ignore

    # crée le graph pygraphviz
    pdestination = Path(destination)
    py_graph = nx.nx_agraph.to_agraph(graph)
    py_graph.draw(pdestination, prog=gv_args["algorithm"], format=pdestination.suffix.strip("."))
