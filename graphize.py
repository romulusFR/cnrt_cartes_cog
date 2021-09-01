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
    compute_cooc_matrix,
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


# logger.debug(f"CONCEPT_IDX['nature'] = {CONCEPT_IDX['nature']}")
# for i in CONCEPT_IDX["nature"]:
#     logger.debug(f"CONCEPT_MAP[{i}] = {CONCEPT_MAP[i]}")
# logger.debug(f"CONCEPT_COOC['nature'] = {CONCEPT_COOC['nature']}")

# BUG perdu les poids des arcs
def generate(pairs, min_threshold=2, max_threshold=5):
    for (carte_file, thesaurus_file) in pairs:
        logger.info(f"carte_file = {carte_file}")
        logger.info(f"thesaurus_file = {thesaurus_file}")

        carte_cog = get_cog_maps(carte_file)
        # carte_idx = pivot_cog_map(carte_cog)

        thesaurus = get_ontology(thesaurus_file)
        carte_mere, _ = apply_ontology(carte_cog, thesaurus, with_unknown=False)
        # carte_mere_idx = pivot_cog_map(carte_mere)

        for (carte, name) in [(carte_cog, "bag"), (carte_mere, "bag_mere")]:
            for threshold in range(min_threshold, max_threshold + 1):
                cooc_matrix = compute_cooc_matrix(carte, threshold)
                cooc_diagonal = {word: cooc_matrix[word][word] for word in cooc_matrix}

                # on charge dans networkx
                cooc_graph = nx.Graph(cooc_matrix)
                # virer les arcs boucles
                cooc_graph.remove_edges_from(nx.selfloop_edges(cooc_graph))
                # pour les noeuds, le poid c'est le nombre de cartes
                # PAS fait par la diagonale de cooc_matrix
                # nx.set_node_attributes(cooc_graph, {w: len(l) for w, l in idx_map.items()}, name="weight")
                nx.set_node_attributes(cooc_graph, cooc_diagonal, name="weight")

                # on génère au format graphml et graphviz
                filename = f"{GRAPH_DIR / Path(carte_file).stem}_{name}_{threshold}"
                logger.info(f"  drawing {filename}")
                logger.info(f"  G:{cooc_graph.number_of_nodes()} mots et {cooc_graph.number_of_edges()} arcs")
                nx.write_graphml(cooc_graph, f"{filename}.graphml")
                draw_graphviz(
                    cooc_graph,
                    f"{filename}.{IMG_FORMAT}",
                    algorithm="sfdp",
                    sep=0.01,
                    fontsize="proportional",
                    node_color="weight",
                    min_edge_penwidths=0.1,
                    max_edge_penwidths=1,
                    min_node_size=0.02,
                    max_node_size=1,
                )


DATASETS = [(CARTES_COG_LA_MINE, THESAURUS_LA_MINE), (CARTES_COG_MINE_FUTUR, THESAURUS_MINE_FUTUR)]

# #
if __name__ == "__main__":
    generate(DATASETS, 5, 5)
    # nx.write_graphml(G, GRAPH_DIR / "network.graphml")
    # draw_graphviz(G, GRAPH_DIR / f"network.{IMG_FORMAT}", algorithm="sfdp", sep=0.01, fontsize = "proportional", node_color="weight", min_edge_penwidths=0.01, max_edge_penwidths=4, min_node_size=0.05, max_node_size=2)
