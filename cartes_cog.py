# pylint: disable = logging-fstring-interpolation, line-too-long
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
    logger.setLevel(logging.DEBUG)

CARTES_COG_LA_MINE = "input/cartes_cog_la_mine.csv"
THESAURUS_LA_MINE = "input/thesaurus_la_mine.csv"
CARTES_COG_MINE_FUTUR = "input/cartes_cog_mine_futur.csv"
THESAURUS_MINE_FUTUR = "input/thesaurus_mine_futur.csv"
OUTPUT_DIR = "output"
DEFAULT_CONCEPT = "__inconnu__"

# TODO : passer à une classe pour les cog maps


def clean(string):
    """Standarisation du nettoyage des chaines"""
    return string.strip().lower()


def get_cog_maps(filename):
    """Charge les cartes depuis le fichier CSV"""
    logger.debug(f"get_cog_maps({filename})")
    carte = {}

    with open(filename, encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";", quotechar='"')
        for row in reader:
            # indice 0 : l'id de la carte
            # indices 1 et suivants : les mots de la carte
            identifier = int(row[0])
            carte[identifier] = {}
            # on élimine les mots vides et NULL
            carte[identifier] = [clean(w) for w in row[1:] if w not in ("NULL", "")]

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
    """Sauvegarde pour chaque position, la liste des mots énoncés et leur nombre d'occurences (le produit de compute_histogram_pos) au format csv"""
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
    """Charge l'ontologie (concept, mot énoncé) dans un dico énoncé -> mère"""
    logger.debug(f"get_ontology({filename})")
    ontology = defaultdict(lambda: DEFAULT_CONCEPT)

    with open(filename, encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=";", quotechar='"')
        for row in reader:
            ontology[clean(row[1])] = clean(row[0])
    logger.info(f"ontologie : {len(ontology.keys())} mots énoncés et {len(set(ontology.values()))} concepts")
    return ontology


def apply_ontology(carte, ontology, *, with_unknown=True):
    """Remplace tous les mots énoncés d'une carte par leur concept mère de l'ontologie"""
    logger.debug(
        f"apply_ontology({len(carte)} cartes, {len(ontology)} concepts thesaurus avec inconnus={with_unknown})"
    )
    carte_mere = {}
    unknown_report = defaultdict(list)
    for k, words in carte.items():
        carte_mere[k] = [clean(ontology[word]) for word in words if (ontology[word] != DEFAULT_CONCEPT or with_unknown)]
        for word in words:
            if ontology[word] == DEFAULT_CONCEPT:
                unknown_report[clean(word)].append(k)
    logger.info(
        f"calcul de {len(carte_mere)} cartes mères : {sum(len(l) for l in carte_mere.values())} mots au total ({'avec' if with_unknown else 'sans'} mots inconnus)"
    )
    logger.info(
        f"{len(unknown_report)} mots inconnus ({DEFAULT_CONCEPT}) présents dans au total {sum(len(l) for l in unknown_report.values())} cartes"
    )

    return carte_mere, unknown_report


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

    # crée le dossier de sortie si besoin
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    # application partielle qui génère un préfixe de nom
    get_name = partial(create_filename, output_dir, cartes_filename)

    # chargement des entrées
    carte = get_cog_maps(cartes_filename)
    ontology = get_ontology(ontologie_filename)

    # stats "sac de mot" et "position" de la carte
    write_histogram_bag(compute_histogram_bag(carte), get_name("occurences"))
    write_histogram_pos(compute_histogram_pos(carte), get_name("positions"))

    # les cartes mères : les cartes dont on a remplacé les mots par les mots mères
    carte_mere, inconnus = apply_ontology(carte, ontology, with_unknown=with_unknown)
    write_carte(carte_mere, get_name("meres"))
    write_carte(inconnus, get_name("inconnus"))

    write_histogram_bag(compute_histogram_bag(carte_mere), get_name("occurences_meres"))
    write_histogram_pos(compute_histogram_pos(carte_mere), get_name("positions_meres"))


def test():
    """tests si hors module"""
    carte_mine = get_cog_maps(CARTES_COG_LA_MINE)
    # pprint(carte_mine)

    # hist_bag = compute_histogram_bag(carte_mine)
    # hist_pos = compute_histogram_pos(carte_mine)
    # write_histogram_bag(hist_bag, "tmp/tmp_hist_bag.csv")
    # write_histogram_pos(hist_pos, "tmp/tmp_hist_pos.csv")
    # # pprint(hist_bag)
    # # pprint(hist_pos)

    ontology_mine = get_ontology(THESAURUS_LA_MINE)
    carte_mine_mere = apply_ontology(carte_mine, ontology_mine, with_unknown=False)
    pprint(carte_mine_mere)

    # hist_bag_mere = compute_histogram_bag(carte_mine_mere)
    # hist_pos_mere = compute_histogram_pos(carte_mine_mere)
    # write_histogram_bag(hist_bag_mere, "tmp/tmp_hist_bag_mere.csv")
    # write_histogram_pos(hist_pos_mere, "tmp/tmp_hist_pos_mere.csv")
    # pprint(hist_bag)
    # pprint(hist_pos)


if __name__ == "__main__":
    # test()
    generate_results(OUTPUT_DIR, CARTES_COG_LA_MINE, THESAURUS_LA_MINE)
    # generate_results(OUTPUT_DIR, CARTES_COG_MINE_FUTUR, THESAURUS_MINE_FUTUR)
