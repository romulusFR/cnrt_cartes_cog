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


from cog_maps import (
    CM_SMALL_FILENAME,
    CM_LA_MINE_FILENAME,
    CM_FUTUR_FILENAME,
    THESAURUS_FILENAME,
    WEIGHTS_MAP_FILENAME,
    LEVELS,
    DEFAULT_WEIGHTS,
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


def generate_all_graphs(maps, thesaurus, weights, *, thresholds=None):
    """Genère un ensemble de graphes

    Pour chaque carte de MAPS
        Pour chaque niveau du thesaurus de LEVELS
            Pour chaque poids de WEIGHTS
                    génère un graph pour chaque niveau de threshold entre min et max (inclus)
    """
    # gère les arguments par défaut
    if thresholds is None:
        thresholds = list(range(2, 6))
    if weights is None:
        weights = [DEFAULT_WEIGHTS]

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

    for cog_maps_map_filename in maps:
        logger.info(f"generate_all_graphs({cog_maps_map_filename})")
        cog_maps = CogMaps(cog_maps_map_filename)
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
# les deux jeus de données
DATASETS = [CM_LA_MINE_FILENAME, CM_FUTUR_FILENAME]

THE_THESAURUS = CogMaps.load_thesaurus_map(THESAURUS_FILENAME)
THE_WEIGHTS = CogMaps.load_weights(WEIGHTS_MAP_FILENAME)

DEMO = True
if __name__ == "__main__":
    if DEMO:
        generate_all_graphs(
            maps=[CM_SMALL_FILENAME],
            thesaurus=THE_THESAURUS,
            weights=THE_WEIGHTS,
            thresholds=[float(n) for n in range(1, 4)],
        )
    else:
        generate_all_graphs(
            maps=DATASETS,
            thesaurus=THE_THESAURUS,
            weights=THE_WEIGHTS,
            thresholds=[float(n) for n in range(2, 4)],
        )
