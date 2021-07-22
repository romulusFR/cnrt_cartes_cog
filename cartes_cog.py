# pylint: disable = logging-fstring-interpolation
"""Outil de traitement des cartes cognitives"""

__author__ = "Romuald Thion"

# %%

import csv
import logging
from collections import Counter, defaultdict
from itertools import product, zip_longest
from functools import partial
from pprint import pprint  # pylint: disable=unused-import
from pathlib import Path

logger = logging.getLogger(f"COGNITIVE_MAP.{__name__}")
if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.INFO)

CARTES_COG_FILE_DEFAULT = "input/bd_mots_enonces.csv"
ONTOLOGIE_FILE_DEFAULT = "input/thesaurus.csv"
OUTPUT_DIR = "output"
DEFAULT_CONCEPT = "concept inconnu"

# TODO : passer à une classe pour les cog maps


def get_cog_maps(filename):
    """Charge les cartes depuis le fichier CSV"""
    logger.debug(f"get_cog_maps({filename})")
    carte = {}

    with open(filename, encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";", quotechar='"')
        for row in reader:
            identifier = int(row[0])
            carte[identifier] = {}
            carte[identifier] = [w.strip().lower() for w in row[1:] if w not in ("NULL", "")]

    logger.info(f"lecture de {len(carte)} cartes : {sum(len(l) for l in carte.values())} mots au total")
    return carte


def write_carte(carte, filename):
    """Ecrit les cartes depuis la map python"""
    logger.debug(f"write_carte({len(carte)}, {filename})")
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=";", quotechar='"')
        for i, words in carte.items():
            writer.writerow([i] + words)
    logger.info(f"cartes mères : {filename}")


def compute_histogram_bag(carte):
    """Calcule le nombre d'occurence de chaque mot dans toutes les cartes"""
    logger.debug(f"compute_histogram_bag({len(carte)})")
    bag = [w for d in carte.values() for w in d]
    hist = Counter(bag).most_common()
    logger.info(f"histogramme du sac de mots : {len(hist)} mots différents dans les cartes")
    return hist


def compute_histogram_pos(carte):
    """Pour chaque position, calcule le nombre d'occurence de chaque mot dans cette position"""
    logger.debug(f"compute_histograms_position({len(carte)})")
    hist = defaultdict(list)
    for i, words in carte.items():
        for j, word in enumerate(words):
            hist[j + 1].append(word)

    for i, words in hist.items():
        hist[i] = Counter(words).most_common()

    logger.info(f"histogramme des positions : {len(hist)} positions (longueur de la plus longue carte)")
    return hist


def write_histogram_bag(hist, filename):
    """Sauvegarde la liste des mots énoncés et leur nombre d'occurences (le produit de compute_histogram_bag) au format csv"""
    logger.debug(f"write_histogram_bag({len(hist)}, {filename})")
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=";", quotechar='"')
        for row in hist:
            writer.writerow(row)
    logger.info(f"histogramme du sac de mots : {filename}")


def write_histogram_pos(hist, filename):
    """Sauvegarde pour chaque position, la liste des mots énoncés et leur nombre d'occurences(le produit de compute_histogram_pos) au format csv"""
    logger.debug(f"write_histogram_pos({len(hist)}, {filename})")
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=";", quotechar='"')
        header = [f"{k} {i}" for i, k in product(hist.keys(), ["mot", "nb"])]
        writer.writerow(header)
        content = zip_longest(*hist.values(), fillvalue=("", ""))
        for row in content:
            writer.writerow([x for pair in row for x in pair])
    logger.info(f"histogramme des positions : {filename}")


def get_ontology(filename):
    """Charge l'ontologie (concept, mot énoncé)"""
    logger.debug(f"get_ontology({filename})")
    ontology = defaultdict(lambda: DEFAULT_CONCEPT)

    with open(filename, encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";", quotechar='"')
        for row in reader:
            ontology[row[1].strip().lower()] = row[0].strip().lower()
    logger.info(f"ontologie : {len(ontology.keys())} mots énoncés et {len(set(ontology.values()))} concepts")
    return ontology


def apply_ontology(carte, ontology, *, with_unknown=True):
    """Remplace tous les mots énoncés d'une carte par leur concept mère de l'ontologie"""
    logger.debug(f"apply_ontology({len(carte)}, {len(ontology), with_unknown})")
    carte_mere = {}
    for k, words in carte.items():
        carte_mere[k] = [ontology[w].strip().lower() for w in words if (ontology[w] != DEFAULT_CONCEPT or with_unknown)]
    logger.info(
        f"calcul de {len(carte_mere)} cartes mères : {sum(len(l) for l in carte_mere.values())} mots au total ({'avec' if with_unknown else 'sans'} mots inconnus)"
    )
    return carte_mere


def create_filename(outdir, base, suffix):
    """Génère un nom de fichier standardisé pour les résultats de calcul"""
    res = Path(outdir) / Path(f"{Path(base).stem}_{suffix}.csv")
    return res


def generate_results(output_dir, cartes_filename, ontologie_filename, with_unknown=False):
    """"programme principal utilisé par la CLI et la GUI"""
    logger.debug(f"output = {output_dir}")
    logger.debug(f"cartes_cognitives = {cartes_filename}")
    logger.debug(f"ontologie = {ontologie_filename}")
    logger.debug(f"with_unknown = {with_unknown}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    get_name = partial(create_filename, output_dir, cartes_filename)

    carte = get_cog_maps(cartes_filename)
    write_histogram_bag(compute_histogram_bag(carte), get_name("occurences"))
    write_histogram_pos(compute_histogram_pos(carte), get_name("positions"))

    ontology = get_ontology(ontologie_filename)
    carte_mere = apply_ontology(carte, ontology, with_unknown=with_unknown)

    write_carte(carte_mere, get_name("meres"))
    write_histogram_bag(compute_histogram_bag(carte_mere), get_name("occurences_meres"))
    write_histogram_pos(compute_histogram_pos(carte_mere), get_name("positions_meres"))


def test():
    """tests si hors module"""
    carte_mine = get_cog_maps(CARTES_COG_FILE_DEFAULT)
    # pprint(carte_mine)

    hist_bag = compute_histogram_bag(carte_mine)
    hist_pos = compute_histogram_pos(carte_mine)
    write_histogram_bag(hist_bag, "tmp/tmp_hist_bag.csv")
    write_histogram_pos(hist_pos, "tmp/tmp_hist_pos.csv")
    # pprint(hist_bag)
    # pprint(hist_pos)

    ontology_mine = get_ontology(ONTOLOGIE_FILE_DEFAULT)
    carte_mine_mere = apply_ontology(carte_mine, ontology_mine, with_unknown=True)
    # pprint(carte_mine_mere)

    hist_bag_mere = compute_histogram_bag(carte_mine_mere)
    hist_pos_mere = compute_histogram_pos(carte_mine_mere)
    write_histogram_bag(hist_bag_mere, "tmp/tmp_hist_bag_mere.csv")
    write_histogram_pos(hist_pos_mere, "tmp/tmp_hist_pos_mere.csv")
    # pprint(hist_bag)
    # pprint(hist_pos)


if __name__ == "__main__":
    # test()
    generate_results("tmp/", CARTES_COG_FILE_DEFAULT, ONTOLOGIE_FILE_DEFAULT)
