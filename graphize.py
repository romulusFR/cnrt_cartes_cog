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


def extend_matrix_to_nx(matrix):
    """etend un dict[mot, dict[mot, int]] en dict[mot, dict[mot, dict[attr, int]]]
    avec un niveau suppl de dict pour l'attribut "weight" que nx demande"""
    return {
        row_word: {col_word: {"weight": matrix[row_word][col_word]} for col_word in matrix[row_word]}
        for row_word in matrix
    }


def generate(pairs, /, thresholds=None, max_window_widths=None):
    """Genère un ensemble de graphes

    Pour chaque paire (carte, thesaurus) de pairs, génère (carte_base, carte_mere)
    puis pour chacune de ces paires, génère un graph pour chaque niveau de threshold entre min et max (inclus)
    """
    # gère les arguments par défaut
    if thresholds is None:
        thresholds = list(range(2, 6))
    if max_window_widths is None:
        max_window_widths = [None]

    for (carte_file, thesaurus_file) in pairs:
        logger.info(f"carte_file = {carte_file}")
        logger.info(f"thesaurus_file = {thesaurus_file}")

        carte_cog = get_cog_maps(carte_file)
        # carte_idx = pivot_cog_map(carte_cog)

        thesaurus = get_ontology(thesaurus_file)
        carte_mere, _ = apply_ontology(carte_cog, thesaurus, with_unknown=False)
        # carte_mere_idx = pivot_cog_map(carte_mere)

        for (carte, name) in [(carte_cog, "bag"), (carte_mere, "bag_mere")]:
            for threshold in thresholds:
                for width in max_window_widths:
                    cooc_matrix = compute_cooc_matrix(carte, min_cooc_threshold=threshold, max_window_width=width)
                    # pprint(cooc_matrix)
                    cooc_diagonal = {word: cooc_matrix[word][word] for word in cooc_matrix}
                    # version étdenu avec un niveau suppl de dict pour "weight"
                    cooc_matrix_ext = extend_matrix_to_nx(cooc_matrix)
                    # on charge dans networkx
                    cooc_graph = nx.Graph(cooc_matrix_ext)
                    # virer les arcs boucles et les isolés
                    cooc_graph.remove_edges_from(nx.selfloop_edges(cooc_graph))
                    cooc_graph.remove_nodes_from(list(nx.isolates(cooc_graph)))
                    # pour les noeuds, le poid c'est le nombre de cartes
                    # PAS fait par la diagonale de cooc_matrix
                    # nx.set_node_attributes(cooc_graph, {w: len(l) for w, l in idx_map.items()}, name="weight")
                    nx.set_node_attributes(cooc_graph, cooc_diagonal, name="weight")

                    # on génère au format graphml et graphviz
                    filename = f"{GRAPH_DIR / Path(carte_file).stem}_{name}_{threshold}_{width}"
                    logger.info(f"  drawing {filename}")
                    logger.info(f"  G:{cooc_graph.number_of_nodes()} mots et {cooc_graph.number_of_edges()} arcs")
                    if cooc_graph.number_of_nodes() == 0:
                        logger.warning(f"empty graph {filename}")
                        continue
                    # else
                    nx.write_graphml(cooc_graph, f"{filename}.graphml")
                    draw_graphviz(
                        cooc_graph,
                        f"{filename}.{IMG_FORMAT}",
                        algorithm="sfdp",
                        sep=0.01,
                        fontsize=8,  # "proportional",
                        node_color="weight",
                        min_edge_penwidths=1,
                        max_edge_penwidths=10,
                        min_node_size=0.02,
                        max_node_size=1,
                    )


# dossier et format de sortie
IMG_FORMAT = "svg"
GRAPH_DIR = Path("graphs/")
Path(GRAPH_DIR).mkdir(parents=True, exist_ok=True)
# nombre minimal de cooc
THRESHOLD = 3
# les deux paire "la mine" et "la mine dans le futur"
DATASETS = [(CARTES_COG_LA_MINE, THESAURUS_LA_MINE), (CARTES_COG_MINE_FUTUR, THESAURUS_MINE_FUTUR)]


if __name__ == "__main__":
    # [("input/cartes_cog_small.csv", THESAURUS_LA_MINE)]
    generate(DATASETS, thresholds=[2, 5, 10], max_window_widths=[1, 2, 3, 4, 5])
    # nx.write_graphml(G, GRAPH_DIR / "network.graphml")
    # draw_graphviz(G, GRAPH_DIR / f"network.{IMG_FORMAT}", algorithm="sfdp", sep=0.01, fontsize = "proportional", node_color="weight", min_edge_penwidths=0.01, max_edge_penwidths=4, min_node_size=0.05, max_node_size=2)
