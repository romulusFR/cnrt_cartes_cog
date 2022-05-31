# pylint: disable = logging-fstring-interpolation, unused-import
"""Génération d'un ensemble de graphes de co-occurence des paires de mots mères. Ici format image / svg"""

__author__ = "Romuald Thion"

# %%
import logging
from math import isclose, exp
from collections import Counter, defaultdict
from functools import partial
from pathlib import Path
from pprint import pprint
from operator import itemgetter

import networkx as nx
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
template = env.get_template("viz/gallerie.jinja2.html")


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


def cog_map_to_graph(a_map, threshold):
    """Etend une cogmap à un graphe Networkx et fait un peu de nettoyage"""
    graph = nx.Graph(extend_matrix_to_nx(a_map.matrix, threshold))
    # BUG : est-ce bien le même ordre ? !
    diagonal = {word: a_map.matrix[word][word] for word in a_map.words}

    # virer les arcs boucles et les isolés
    graph.remove_edges_from(nx.selfloop_edges(graph))
    graph.remove_nodes_from(list(nx.isolates(graph)))
    # pour les noeuds, le poid c'est le nombre de cartes
    # PAS fait par la diagonale de cooc_matrix
    nx.set_node_attributes(graph, diagonal, name="weight")
    return graph


def generate_all_graphs(cog_maps_filenames, thesaurus, weights_map, *, thresholds=None):
    """Genère un ensemble de graphes

    Pour chaque carte de MAPS
        Pour chaque niveau du thesaurus de LEVELS
            Pour chaque poids de WEIGHTS
                    génère un graph pour chaque niveau de threshold entre min et max (inclus)
    """
    # gère les arguments par défaut
    if thresholds is None:
        thresholds = list(range(2, 6))
    if weights_map is None:
        weights = {"all_1": DEFAULT_WEIGHTS}

    # fonction pour dessiner
    draw = partial(
        draw_graphviz,
        algorithm="sfdp",
        sep=0.01,
        fontsize="proportional",  # "proportional",
        node_color="weight",
        min_edge_penwidths=1,
        max_edge_penwidths=10,
        min_node_size=0.02,
        max_node_size=1,
    )

    report = {}
    base_indent = 2
    for filename in cog_maps_filenames:
        logger.info(f"generate_all_graphs: processing{filename}")
        cog_maps = CogMaps(filename)
        all_maps, _ = cog_maps.apply_many(thesaurus)
        for level_name, a_map in all_maps.items():
            logger.debug(f"{' '*base_indent*1}->{level_name}")
            for weights_name, weights in weights_map.items():
                logger.debug(f"{' '*base_indent*2}->{weights_name}")
                a_map.weights = weights
                export_name = f"{GRAPH_DIR / Path(filename).stem}_{level_name}_{weights_name}"
                # a_map.dump_matrix(f"{export_name}.csv")
                for threshold in thresholds:
                    logger.debug(f"{' '*base_indent*3}->{threshold}")
                    graph = cog_map_to_graph(a_map, threshold)
                    full_export_name = f"{export_name}_{threshold}.{IMG_FORMAT}"
                    # on génère au format graphml et graphviz
                    report[(Path(filename).name, level_name, weights_name, threshold)] = (
                        Path(full_export_name).name,
                        graph.number_of_nodes(),
                        graph.number_of_edges(),
                    )
                    if graph.number_of_nodes() == 0:
                        logger.warning(f"empty graph {export_name}_{threshold}")
                        continue
                    # else
                    # nx.write_graphml(graph, f"{filename}.graphml")
                    logger.info(f"{' '*base_indent*3}*{full_export_name}*")
                    if DRAW:
                        draw(graph, full_export_name)
    return report


def render(content):
    """Génére une gallerie des images svg avec Jinja"""
    print(f"{len(content) = }")
    helper = lambda i: sorted(set(cont[i] for cont in content.keys()))
    dimensions = {
        "filenames": helper(0),
        "levels": helper(1),
        "weights": helper(2),
        "thresholds": helper(3),
    }
    pprint(dimensions)

    html_content = template.render(dimensions=dimensions, content=content)
    # on enregistre le fichier produit sur le disque
    fichier = "viz/gallerie.html"
    with open(fichier, mode="w", encoding="utf-8") as file:
        file.write(html_content)


# dossier et format de sortie
IMG_FORMAT = "svg"  # "png"
GRAPH_DIR = Path("graphs/")
Path(GRAPH_DIR).mkdir(parents=True, exist_ok=True)
# nombre minimal de cooc
THRESHOLD = 3
# les deux jeus de données
DATASETS = [CM_LA_MINE_FILENAME, CM_FUTUR_FILENAME]

THE_THESAURUS = CogMaps.load_thesaurus_map(THESAURUS_FILENAME)
THE_WEIGHTS = CogMaps.load_weights(WEIGHTS_MAP_FILENAME)

DRAW = True
DEMO = False
if __name__ == "__main__":
    if DEMO:
        report = generate_all_graphs(
            cog_maps_filenames=DATASETS,  # ["input/cartes_cog_small_cooc.csv"],
            thesaurus=THE_THESAURUS,
            weights_map={"exponentielle": THE_WEIGHTS["exponentielle"]},
            thresholds=[float(n) for n in range(9, 10)],
        )
    else:
        report = generate_all_graphs(
            cog_maps_filenames=DATASETS,  # DATASETS[0:1],
            thesaurus=THE_THESAURUS,
            weights_map={
                name: weights
                for name, weights in THE_WEIGHTS.items()
                if name in ["arithmetique", "inverse", "exponentielle"]
            },
            thresholds=[float(n) for n in range(6, 12)],
        )
    # pprint(report)
    render(report)
