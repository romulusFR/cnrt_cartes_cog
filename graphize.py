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
    CARTES_COG_MINE_FUTUR,
    THESAURUS_LA_MINE,
    THESAURUS_MINE_FUTUR,
    apply_ontology,
    generate_results,
    get_cog_maps,
    get_ontology,
    pivot_cog_map,
)
from draw_graphviz import draw_graphviz

logger = logging.getLogger(f"COGNITIVE_MAP.{__name__}")
if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.INFO)

# cartes considérées
# COG_MAP = get_cog_maps(CARTES_COG_LA_MINE)
# ONTOLOGY = get_ontology(THESAURUS_LA_MINE)
COG_MAP = get_cog_maps(CARTES_COG_MINE_FUTUR)
ONTOLOGY = get_ontology(THESAURUS_MINE_FUTUR)


CONCEPT_MAP, EERROR_MAP = apply_ontology(COG_MAP, ONTOLOGY, with_unknown=False)

# dossier et format de sortie
IMG_FORMAT = "svg"
GRAPH_DIR = Path("graphs/")
Path(GRAPH_DIR).mkdir(parents=True, exist_ok=True)

# nombre minimal de cooc
THRESHOLD = 3

CONCEPT_IDX = pivot_cog_map(CONCEPT_MAP)

logger.debug(f"CONCEPT_MAP = {CONCEPT_MAP}")
logger.debug(f"CONCEPT_IDX = { {w:len(l) for w, l in CONCEPT_IDX.items()} }")
logger.info(f"{len(CONCEPT_IDX)} concepts")





def cooc(cog_map_idx, threshold = 2):
    # dictionnaire des co-occurrences :
    # à chaque mot (lignes)
    #   -> un dictionnaire qui à chaque mot colonne
    #       -> un dictionnaire qui à chaque attribut
    #           -> donne dans "weight" le nombre de cartes où on apparait en commun
    # un dictionnaire de plus que nécessaire pour être compatible avec l'API networkx
    cooc_map = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # type: ignore

    for word_row in cog_map_idx:
        for word_col in cog_map_idx:
            common_times = sum((Counter(cog_map_idx[word_row]) & Counter(cog_map_idx[word_col])).values())
            if common_times >= threshold and word_row != word_col:
                cooc_map[word_row][word_col]["weight"] = common_times
    return cooc_map

# logger.debug(f"CONCEPT_IDX['nature'] = {CONCEPT_IDX['nature']}")
# for i in CONCEPT_IDX["nature"]:
#     logger.debug(f"CONCEPT_MAP[{i}] = {CONCEPT_MAP[i]}")
# logger.debug(f"CONCEPT_COOC['nature'] = {CONCEPT_COOC['nature']}")

CONCEPT_COOC = cooc(CONCEPT_IDX, THRESHOLD)
# TODO ici un lifting d'une structure plus naturelle
# on charge dans graphviz
G = nx.Graph(CONCEPT_COOC)
# pour les noeuds, le poid c'est le nombre de cartes
nx.set_node_attributes(G, {w: len(l) for w, l in CONCEPT_IDX.items()}, name="weight")

logger.info(nx.info(G))
if __name__ == "__main__":
    # nx.write_graphml(G, GRAPH_DIR / "network.graphml")
    draw_graphviz(G, GRAPH_DIR / f"network.{IMG_FORMAT}", algorithm="sfdp", sep=0.01, fontsize = "proportional", node_color="weight", min_edge_penwidths=0.01, max_edge_penwidths=4)
