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
    logger.setLevel(logging.DEBUG)

COG_MAP = get_cog_maps(CARTES_COG_LA_MINE)
ONTOLOGY = get_ontology(THESAURUS_LA_MINE)
CONCEPT_MAP, EERROR_MAP = apply_ontology(COG_MAP, ONTOLOGY, with_unknown=False)

# dossier et format de sortie
IMG_FORMAT = "svg"
GRAPH_DIR = Path("graphs/")
Path(GRAPH_DIR).mkdir(parents=True, exist_ok=True)

# on pivote CONCEPT_MAP en CONCEPT_IDX
# à chaque mot les id des cartes où il apparait
CONCEPT_IDX = defaultdict(list)
for identifier, words in CONCEPT_MAP.items():
    for word in words:
        CONCEPT_IDX[word].append(identifier)

logger.debug(f"CONCEPT_MAP = {CONCEPT_MAP}")
logger.debug(f"CONCEPT_IDX = { {w:len(l) for w, l in CONCEPT_IDX.items()} }")
logger.info(f"{len(CONCEPT_IDX)} concepts")


# dictionnaire des co-occurrences :
# à chaque mot (lignes)
#   -> un dictionnaire qui à chaque mot colonne
#       -> un dictionnaire qui à chaque attribut
#           -> donne dans "weight" le nombre de cartes où on apparait en commun
# un dictionnaire de plus que nécessaire pour être compatible avec l'API networkx
CONCEPT_COOC = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # type: ignore

# nombre minimal de cooc
THRESHOLD = 5

for word_row in CONCEPT_IDX:
    for word_col in CONCEPT_IDX:
        common_times = sum((Counter(CONCEPT_IDX[word_row]) & Counter(CONCEPT_IDX[word_col])).values())
        if common_times >= THRESHOLD and word_row != word_col:
            CONCEPT_COOC[word_row][word_col]["weight"] = common_times

# logger.debug(f"CONCEPT_IDX['nature'] = {CONCEPT_IDX['nature']}")
# for i in CONCEPT_IDX["nature"]:
#     logger.debug(f"CONCEPT_MAP[{i}] = {CONCEPT_MAP[i]}")
# logger.debug(f"CONCEPT_COOC['nature'] = {CONCEPT_COOC['nature']}")



# on charge dans graphviz
G = nx.Graph(CONCEPT_COOC)
# pour les noeuds, le poid c'est le nombre de cartes
nx.set_node_attributes(G, {w: len(l) for w, l in CONCEPT_IDX.items()}, name="weight")

logger.info(nx.info(G))
# nx.write_graphml(G, GRAPH_DIR / "network.graphml")
if __name__ == "__main__":
    draw_graphviz(G, GRAPH_DIR / f"network.{IMG_FORMAT}", algorithm="sfdp", sep=0.01, fontsize = "proportional", node_color="weight", min_edge_penwidths=0.01, max_edge_penwidths=4)
