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
    pivot_cog_map_bag,
)
from draw_graphviz import draw_graphviz

logger = logging.getLogger(f"COGNITIVE_MAP.{__name__}")
if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.INFO)

# cartes considérées
# COG_MAP = get_cog_maps(CARTES_COG_LA_MINE)
# ONTOLOGY = get_ontology(THESAURUS_LA_MINE)
# COG_MAP = get_cog_maps(CARTES_COG_MINE_FUTUR)
# ONTOLOGY = get_ontology(THESAURUS_MINE_FUTUR)


# dossier et format de sortie
IMG_FORMAT = "svg"
GRAPH_DIR = Path("graphs/")
Path(GRAPH_DIR).mkdir(parents=True, exist_ok=True)

# nombre minimal de cooc
THRESHOLD = 3

# CONCEPT_MAP, ERROR_MAP = apply_ontology(COG_MAP, ONTOLOGY, with_unknown=False)
# CONCEPT_IDX = pivot_cog_map_bag(CONCEPT_MAP)

# logger.debug(f"CONCEPT_MAP = {CONCEPT_MAP}")
# logger.debug(f"CONCEPT_IDX = { {w:len(l) for w, l in CONCEPT_IDX.items()} }")
# logger.info(f"{len(CONCEPT_IDX)} concepts")

# TODO ici un lifting d'une structure plus naturelle
def cooc(cog_map_idx, threshold=2):
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


def generate(pairs, min_threshold=2, max_threshold=5):
    for (carte_file, thesaurus_file) in pairs:
        logger.info(f"carte_file = {carte_file}")
        logger.info(f"thesaurus_file = {thesaurus_file}")

        carte_cog = get_cog_maps(carte_file)
        carte_idx = pivot_cog_map_bag(carte_cog)

        thesaurus = get_ontology(thesaurus_file)
        carte_mere, _ = apply_ontology(carte_cog, thesaurus, with_unknown=False)
        carte_mere_idx = pivot_cog_map_bag(carte_mere)

        for (idx_map, name) in [(carte_idx, "bag"), (carte_mere_idx, "bag_mere")]:
            for threshold in range(min_threshold, max_threshold + 1):
                cooc_matrix = cooc(idx_map, threshold)
                # on charge dans networkx
                cooc_graph = nx.Graph(cooc_matrix)
                # pour les noeuds, le poid c'est le nombre de cartes
                nx.set_node_attributes(cooc_graph, {w: len(l) for w, l in idx_map.items()}, name="weight")
                # on génère au format graphviz
                # nx.write_graphml(cooc_graph, GRAPH_DIR / "network.graphml")
                filename = f"{Path(carte_file).stem}_{name}_{threshold}"
                logger.info(f"  drawing {filename}")
                logger.info(f"  G:{cooc_graph.number_of_nodes()} mots et {cooc_graph.number_of_edges()} arcs")
                draw_graphviz(
                    cooc_graph,
                    GRAPH_DIR / f"{filename}.{IMG_FORMAT}",
                    algorithm="sfdp",
                    sep=0.01,
                    fontsize="proportional",
                    node_color="weight",
                    min_edge_penwidths=0.1,
                    max_edge_penwidths=10,
                    min_node_size=0.02,
                    max_node_size=1,
                )


DATASETS = [(CARTES_COG_LA_MINE, THESAURUS_LA_MINE), (CARTES_COG_MINE_FUTUR, THESAURUS_MINE_FUTUR)]

# #
if __name__ == "__main__":
    generate(DATASETS)
    # nx.write_graphml(G, GRAPH_DIR / "network.graphml")
    # draw_graphviz(G, GRAPH_DIR / f"network.{IMG_FORMAT}", algorithm="sfdp", sep=0.01, fontsize = "proportional", node_color="weight", min_edge_penwidths=0.01, max_edge_penwidths=4, min_node_size=0.05, max_node_size=2)
