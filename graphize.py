# pylint: disable = logging-fstring-interpolation, unused-import
"""génération de graphe de co-occurence des paire de mots mères"""

__author__ = "Romuald Thion"

import logging

# %%
from collections import Counter, defaultdict
from pathlib import Path
from pprint import pprint

import networkx as nx


from cartes_cog import (
    CARTES_COG_LA_MINE,
    THESAURUS_LA_MINE,
    apply_ontology,
    generate_results,
    get_cog_maps,
    get_ontology,
)
from draw_graphviz import draw_graphviz

logger = logging.getLogger(f"COGNITIVE_MAP.{__name__}")
if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.INFO)

COG_MAP = get_cog_maps(CARTES_COG_LA_MINE)
ONTOLOGY = get_ontology(THESAURUS_LA_MINE)
CONCEPT_MAP, EERROR_MAP = apply_ontology(COG_MAP, ONTOLOGY, with_unknown=False)

logger.debug(f"CONCEPT_MAP = {CONCEPT_MAP}")

# dossier et format de sortie
IMG_FORMAT = "svg"
GRAPH_DIR = Path("graphs/")
Path(GRAPH_DIR).mkdir(parents=True, exist_ok=True)

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


G = nx.Graph(CONCEPT_COOC)
nx.set_node_attributes(G, {w: len(l) for w, l in CONCEPT_IDX.items()}, name="weight")

logger.info(nx.info(G))
nx.write_graphml(G, GRAPH_DIR / "network.graphml")


if __name__ == "__main__":
    draw_graphviz(G, GRAPH_DIR / f"network.{IMG_FORMAT}", algorithm="sfdp", sep=0.01, fontsize = "proportional", node_color="weight", min_edge_penwidths=0.01, max_edge_penwidths=4)
