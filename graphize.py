# pylint: disable = logging-fstring-interpolation, unused-import
"""génération de graphe de co-occurence des paire de mots mères"""

__author__ = "Romuald Thion"

import logging

# %%
from math import isclose, exp
from collections import Counter, defaultdict
from functools import partial
from pathlib import Path
from pprint import pprint

import networkx as nx


from cartes_cog import (
    CARTES_COG_LA_MINE,
    CARTES_COG_MINE_FUTUR,
    THESAURUS_LA_MINE,
    THESAURUS_MINE_FUTUR,
    WEIGHTED_POSITIONS,
    WEIGHTS,
    CogMaps,
)
from draw_graphviz import draw_graphviz

logger = logging.getLogger(f"COGNITIVE_MAP.{__name__}")
if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.INFO)


def extend_matrix_to_nx(matrix, threshold=0.0):
    """etend un dict[mot, dict[mot, int]] en dict[mot, dict[mot, dict[attr, int]]]
    avec un niveau suppl de dict pour l'attribut "weight" que nx demande"""
    return {
        row_word: {
            col_word: {"weight": matrix[row_word][col_word]}
            for col_word in matrix[row_word]
            # if not isclose(matrix[row_word][col_word], 0.0)
            if matrix[row_word][col_word] >= threshold
        }
        for row_word in matrix
    }


def generate_all_graphs(pairs, /, thresholds=None, weights=None):
    """Genère un ensemble de graphes

    Pour chaque paire (carte, thesaurus) de pairs, génère (carte_base, carte_mere)
    puis pour chacune de ces paires, génère un graph pour chaque niveau de threshold entre min et max (inclus)
    """
    # gère les arguments par défaut
    if thresholds is None:
        thresholds = list(range(2, 6))
    if weights is None:
        weights = [None]

    # fonction pour dessiner
    draw = partial(
        draw_graphviz,
        algorithm="sfdp",
        sep=0.01,
        fontsize=8,  # "proportional",
        node_color="weight",
        min_edge_penwidths=1,
        max_edge_penwidths=10,
        min_node_size=0.02,
        max_node_size=1,
    )

    report = {}

    for (carte_file, thesaurus_file) in pairs:
        logger.info(f"carte_file = {carte_file}")
        logger.info(f"thesaurus_file = {thesaurus_file}")

        cog_maps = CogMaps(carte_file, thesaurus_file)
        concept_maps, _ = cog_maps.apply(with_unknown=False)

        for (maps, maps_name) in [(cog_maps, "base"), (concept_maps, "concept")]:
            # cartes.weights = defaultdict(lambda : 1)
            for weights_name, weights_def in weights.items():
                maps.weights = weights_def
                matrix = maps.matrix
                maps.dump_matrix(f"{GRAPH_DIR / Path(carte_file).stem}_{maps_name}_{weights_name}.csv")

                for threshold in thresholds:
                    graph = nx.Graph(extend_matrix_to_nx(matrix, threshold))
                    diagonal = {word: matrix[word][word] for word in maps.words}

                    # virer les arcs boucles et les isolés
                    graph.remove_edges_from(nx.selfloop_edges(graph))
                    graph.remove_nodes_from(list(nx.isolates(graph)))
                    # pour les noeuds, le poid c'est le nombre de cartes
                    # PAS fait par la diagonale de cooc_matrix
                    nx.set_node_attributes(graph, diagonal, name="weight")

                    # on génère au format graphml et graphviz
                    # filename = f"{GRAPH_DIR / Path(carte_file).stem}_{name}_{threshold}_{width}"
                    filename = f"{GRAPH_DIR / Path(carte_file).stem}_{maps_name}_{threshold}_{weights_name}"
                    report[(maps_name, threshold, weights_name)] = (graph.number_of_nodes(), graph.number_of_edges())
                    logger.info(f"  drawing {filename}")
                    logger.info(f"  G:{graph.number_of_nodes()} mots et {graph.number_of_edges()} arcs")
                    if graph.number_of_nodes() == 0:
                        logger.warning(f"empty graph {filename}")
                        continue
                    # else
                    # nx.write_graphml(graph, f"{filename}.graphml")
                    draw(graph, f"{filename}.{IMG_FORMAT}")
    return report


# dossier et format de sortie
IMG_FORMAT = "svg"
GRAPH_DIR = Path("graphs/")
Path(GRAPH_DIR).mkdir(parents=True, exist_ok=True)
# nombre minimal de cooc
THRESHOLD = 3
# les deux paire "la mine" et "la mine dans le futur"
DATASETS = [(CARTES_COG_LA_MINE, THESAURUS_LA_MINE), (CARTES_COG_MINE_FUTUR, THESAURUS_MINE_FUTUR)]


if __name__ == "__main__":
    generate_all_graphs(
        DATASETS[0:1:],
        thresholds=[float(n) for n in range(2, 4)],
        weights={"1_on_n_square": {i: 1 / (i ** 2) for i in range(1, 16)}},
    )
