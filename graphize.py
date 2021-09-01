# pylint: disable = logging-fstring-interpolation
"""génération de graphe de co-occurence des paire de mots mères"""

__author__ = "Romuald Thion"

# %%
from collections import defaultdict, Counter
from pprint import pprint
import logging
from cartes_cog import (
    generate_results,
    CARTES_COG_LA_MINE,
    THESAURUS_LA_MINE,
    apply_ontology,
    get_cog_maps,
    get_ontology,
)

logger = logging.getLogger(f"COGNITIVE_MAP.{__name__}")
if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

COG_MAP = get_cog_maps(CARTES_COG_LA_MINE)
ONTOLOGY = get_ontology(THESAURUS_LA_MINE)
CONCEPT_MAP, EERROR_MAP = apply_ontology(COG_MAP, ONTOLOGY, with_unknown=False)

logger.debug(f"CONCEPT_MAP = {CONCEPT_MAP}")


# on pivote CONCEPT_MAP en CONCEPT_IDX
CONCEPT_IDX = defaultdict(list)
for i, l in CONCEPT_MAP.items():
    for w in l:
        CONCEPT_IDX[w].append(i)


logger.info(f"{len(CONCEPT_IDX)} concepts")
logger.debug(f"CONCEPT_IDX = { {w:len(l) for w, l in CONCEPT_IDX.items()} }")

# %%
CONCEPT_COOC = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # type: ignore

THRESHOLD = 2
# matrix 49 x 49 = 2401
for w1 in CONCEPT_IDX:
    for w2 in CONCEPT_IDX:
        # inter = CONCEPT_IDX[w1], CONCEPT_IDX[w2]
        common_times = sum((Counter(CONCEPT_IDX[w1]) & Counter(CONCEPT_IDX[w2])).values())
        if common_times >= THRESHOLD and w1 != w2:
            CONCEPT_COOC[w1][w2]["weight"] = common_times

# pprint(CONCEPT_COOC)

logger.debug(f"CONCEPT_IDX['nature'] = {CONCEPT_IDX['nature']}")
for i in CONCEPT_IDX["nature"]:
    logger.debug(f"CONCEPT_MAP[{i}] = {CONCEPT_MAP[i]}")
logger.debug(f"CONCEPT_COOC['nature'] = {CONCEPT_COOC['nature']}")


# %%
import networkx as nx
import matplotlib.pyplot as plt


G = nx.Graph(CONCEPT_COOC)
nx.set_node_attributes(G, {w: len(l) for w, l in CONCEPT_IDX.items()}, name="weight")

logger.info(nx.info(G))
nx.write_graphml(G, "graphs/network.graphml")

# %%

# node_options = {
#     "node_size": 50,
#     "linewidths": 0,
#     # "with_labels": False,
# }
# edge_options = {
#     "width": 0.1,
# }
# label_options = {
#     "font_size": 8,
# }

# all_options = {**node_options, **edge_options, **label_options}

# plt.subplots(figsize=(10, 10))
# pos_G = nx.spring_layout(G, k=15)  #

# # le dict des disciplines info (sous ensemble de discs_map) : code -> label@en
# nx.draw(G, pos=pos_G, with_labels=True, **all_options)
# # plt.savefig(f"plots/cooccurrences-threshold-{THRESHOLD}.svg")
# plt.show()


# %%
from functools import wraps
from time import time


def measure(func):
    """From https://stackoverflow.com/questions/51503672/decorator-for-timeit-timeit-method"""

    @wraps(func)
    def _time_it(*args, **kwargs):
        start = int(round(time() * 1_000))
        try:
            return func(*args, **kwargs)
        finally:
            end_ = int(round(time() * 1_000)) - start
            logging.info(f"{func.__name__}() execution time: {end_ if end_ > 0 else 0} ms")

    return _time_it


# %%
import numpy as np
import matplotlib.colors as colors
from pathlib import Path


def draw_graphviz(
    a_graph: nx.Graph, /, node_color: str = None, algorithm: str = "sfdp", sep_param: float = -0.45, k_param: int = 1
) -> None:
    """Generates dot and svg using (py)graphviz

    Parameters
    ----------
    a_graph : nx.Graph
        the graph to draw
    node_color : str, optional
        the ndoe attribute from which color is computed, by default None

    Returns
    -------
    int
        graphviz (twopi) return code
    """

    # on fait une copie car on va modifier bcp d'attribut pour avoir le graphviz
    graph = a_graph.copy()
    node_names = {w: w for w in graph}
    colormap = plt.cm.get_cmap("inferno")  # plasma

    default_edge_size = 0.1
    if nx.is_weighted(graph):
        # on va interpoler les tailles des arcs proportionnel au poids
        edge_weights = nx.get_edge_attributes(graph, "weight")
        min_edge_weight = min(edge_weights.values())
        max_edge_weight = max(edge_weights.values())
        edge_penwidths = {
            e: np.interp(v, [min_edge_weight, max_edge_weight], [0.2, 2]) for e, v in edge_weights.items()
        }
    else:
        edge_penwidths = {k: default_edge_size for k in graph.edges}

    # idem pour la taille des noeuds
    inch_factor = 96
    min_node_size = 10 / inch_factor
    max_node_size = min_node_size * 4
    node_nbs = nx.get_node_attributes(graph, "weight")
    min_node_nb = min(node_nbs.values())
    max_node_nb = max(node_nbs.values())

    def compute_size(value):
        return round(np.interp(value, [min_node_nb, max_node_nb], [min_node_size, max_node_size]), 1)

    node_gwidths = {n: compute_size(v) for n, v in node_nbs.items()}

    # graph.graph["fontsize"] = 14
    graph.graph["fontname"] = "Helvetica"
    graph.graph["bgcolor"] = "white"
    graph.graph["sep"] = sep_param  # TODO : ici pour jouer sur le rapprichement de snoeuds en scale
    # -0.4 : OK pour H2
    graph.graph["overlap"] = "scale"  # "false" #scale false prism
    graph.graph["K"] = k_param

    nx.set_node_attributes(graph, values=round(min_node_size * inch_factor / 5), name="penwidth")
    nx.set_node_attributes(graph, values=0, name="margin")
    nx.set_node_attributes(graph, values=10, name="fontsize")
    nx.set_node_attributes(graph, values="grey30", name="fontcolor")
    nx.set_node_attributes(graph, values="circle", name="shape")
    nx.set_node_attributes(graph, values="shape", name="fixedsize")
    nx.set_node_attributes(graph, values="filled", name="style")
    nx.set_node_attributes(graph, values="white", name="color")
    nx.set_node_attributes(graph, values=node_gwidths, name="width")
    nx.set_node_attributes(graph, values="Helvetica", name="fontname")
    nx.set_node_attributes(graph, values="", name="label")
    nx.set_node_attributes(graph, values=node_names, name="xlabel")

    if node_color is None:
        node_colors = {k: "blue" for k in graph}
        node_label = {k: "" for k in graph}
    else:
        color_attr = nx.get_node_attributes(graph, node_color)
        color_norm = colors.Normalize(vmin=min(color_attr.values()), vmax=max(color_attr.values()))
        node_colors = {k: colors.rgb2hex(colormap(color_norm(v))) for k, v in color_attr.items()}
        node_label = nx.get_node_attributes(graph, "cluster")

    nx.set_node_attributes(graph, values=node_label, name="label")
    nx.set_node_attributes(graph, values=node_colors, name="fillcolor")

    nx.set_edge_attributes(graph, values=edge_penwidths, name="penwidth")
    nx.set_edge_attributes(graph, values="darkgrey", name="color")
    nx.set_edge_attributes(graph, values=default_edge_size / 2, name="arrowsize")

    img_ext = "svg"
    img_file = Path(f"{'graphs/network'}.{img_ext}")

    GV = nx.nx_agraph.to_agraph(graph)
    GV.draw(img_file, prog=algorithm, format=img_ext)


draw_graphviz(G, sep_param=0.2, node_color="weight")
