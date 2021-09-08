# pylint: disable = logging-fstring-interpolation, line-too-long, unused-import
"""Outil de traitement des cartes cognitives"""

__author__ = "Romuald Thion"

# %%

import csv
import logging
from typing import Union
from collections import Counter, defaultdict
from itertools import product, zip_longest
from functools import partial
from pprint import pprint  # pylint: disable=unused-import
from pathlib import Path

# import pandas as pd

logger = logging.getLogger(f"COGNITIVE_MAP.{__name__}")
if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

CARTES_COG_LA_MINE = "input/cartes_cog_la_mine.csv"
THESAURUS_LA_MINE = "input/thesaurus_la_mine.csv"
CARTES_COG_MINE_FUTUR = "input/cartes_cog_mine_futur.csv"
THESAURUS_MINE_FUTUR = "input/thesaurus_mine_futur.csv"
WEIGHTED_POSITIONS = "input/coefficients.csv"
OUTPUT_DIR = "output"
DEFAULT_CONCEPT = "__inconnu__"


CSV_PARAMS = {"delimiter": ";", "quotechar": '"'}
ENCODING = "utf-8"


class CogMaps:
    """Conteneur pour un ensemble de cartes cognitives"""

    # listes des mots considérés comme vides et exlcus de la carte
    EMPTY_WORDS = ("NULL", "")
    """Mots vides"""

    def __init__(self, filename=None):
        self.filename = None
        self.cog_maps: dict[int, list[str]] = {}
        self.cog_index = defaultdict(list)
        if filename is not None:
            self.load(filename)

    @staticmethod
    def clean_word(string: str):
        """Standarisation du nettoyage des chaines"""
        return string.strip().lower()

    def __len__(self):
        return len(self.cog_maps)

    def load(self, filename: Union[Path, str]):
        """Charge les cartes depuis le fichier CSV"""
        logger.debug(f"CogMap.load({filename})")

        with open(filename, encoding=ENCODING) as csvfile:
            reader = csv.reader(csvfile, **CSV_PARAMS)
            for row in reader:
                # indice 0 : l'id de la carte
                # indices 1 et suivants : les mots de la carte
                identifier = int(row[0])
                # on élimine les mots vides et NULL
                self.cog_maps[identifier] = [CogMaps.clean_word(w) for w in row[1:] if w not in CogMaps.EMPTY_WORDS]

        logger.info(
            f"CogMap.load: {len(self.cog_maps)} maps with {sum(len(l) for l in self.cog_maps.values())} total words"
        )
        return self

    def dump(self, filename: Union[Path, str]):
        """Ecrit les cartes depuis la map python"""
        logger.debug(f"CogMap.dump({len(self)}, {filename})")
        with open(filename, "w", newline="", encoding=ENCODING) as csvfile:
            writer = csv.writer(csvfile, **CSV_PARAMS)
            for i, words in self.cog_maps.items():
                writer.writerow([i] + words)  # type: ignore
        logger.info(f"CogMap.dump to {filename}")
        return self

    def pivot(self):
        """Pivote cartes : pour chaque mot, donne les couples (id, pos) des cartes où il apparait"""
        for identifier, words in self.cog_maps.items():
            for pos, word in enumerate(words):
                value = (identifier, pos)
                self.cog_index[word].append(value)
        return self


    def hist(self):
        """Calcule l'histogramme : le nombre d'occurences de chaque mot dans toutes les cartes"""
        logger.debug(f"CogMap.hist({len(self)})")
        bag = [w for d in self.cog_maps.values() for w in d]
        hist = Counter(bag)
        logger.info(f"histogramme du sac de mots : {len(hist)} mots différents dans les cartes")
        return hist


# def get_weights(filename):
#     """Charge les poids depuis le fichier CSV"""
#     logger.debug(f"get_weigths({filename})")
#     weights = defaultdict(float)
#     with open(filename, encoding="utf-8") as csvfile:
#         reader = csv.reader(csvfile, **CSV_PARAMS)
#         _ = next(reader)
#         for row in reader:
#             weights[int(row[0])] = float(row[1])
#     return weights


# def compute_cooc_matrix(cog_map, *, min_cooc_threshold=1, max_window_width=None):
#     """Calcule la matrice de co-occurrece à partir d'une carte pivotée"""
#     # dictionnaire des co-occurrences :
#     # qui à chaque mot ligne
#     #   -> un dictionnaire qui à chaque mot colonne
#     #       -> le nombre de cartes où on apparait en commun
#     # un dictionnaire de plus que nécessaire pour être compatible avec l'API networkx
#     cooc_map = defaultdict(lambda: defaultdict(int))  # type: ignore
#     cog_map_idx = pivot_cog_map(cog_map, with_pos=max_window_width is not None)
#     for word_row in cog_map_idx:
#         for word_col in cog_map_idx:
#             # on va calculer une forme d'intersection multiset avec le &
#             # c & d = forall x. min(c[x], d[x])
#             # https://docs.python.org/3/library/collections.html#collections.Counter
#             # on passe par les counter/multiset car après calcul de la carte mere
#             # on peut avoir plusieurs fois le même mot dans une carte
#             hist_row = Counter(cog_map_idx[word_row])
#             hist_col = Counter(cog_map_idx[word_col])
#             # dans le cas où on a oublié les positions, c'est vraiment le &
#             if max_window_width is None:
#                 common_times = sum((hist_row & hist_col).values())
#             else:
#                 common_times = 0
#                 # logger.debug("%s %s", word_row, hist_row)
#                 # logger.debug("%s %s", word_col, hist_col)
#                 # les paires de paires (id_row, pos_row), (id_col, pos_col)
#                 pos_prod = product(hist_row, hist_col)
#                 # logger.debug("%s %s %s", word_col, word_col, list(pos_prod))
#                 # on est ensemble si on est dans la même carte et
#                 # à une distance de position <= à la taille de la fenetre
#                 def common(row_pair, col_pair):
#                     same_map = row_pair[0] == col_pair[0]
#                     near = abs(row_pair[1] - col_pair[1]) <= max_window_width
#                     return same_map and near

#                 filtered_prod = [min(hist_row[rp], hist_col[cp]) for (rp, cp) in pos_prod if common(rp, cp)]
#                 common_times = sum(filtered_prod)
#             if common_times >= min_cooc_threshold:  # and word_row != word_col
#                 cooc_map[word_row][word_col] = common_times
#     return cooc_map


# def write_cooc_matrix(matrix, filename):
#     """Ecrit les cartes depuis le dict/dic python"""
#     logger.debug(f"write_cooc_matrix({len(matrix)}, {filename})")
#     words = list(sorted(matrix.keys()))
#     with open(filename, "w", newline="", encoding="utf-8") as csvfile:
#         writer = csv.writer(csvfile, **CSV_PARAMS)
#         writer.writerow(["/"] + words)
#         for row_word in words:
#             writer.writerow([row_word] + [matrix[row_word][col_word] for col_word in words])
#     logger.info(f"cartes mères : {filename}")




# def compute_histogram_pos(carte):
#     """Pour chaque position, calcule le nombre d'occurence de chaque mot dans cette position"""
#     logger.debug(f"compute_histograms_position({len(carte)})")
#     hist = defaultdict(list)
#     for i, words in carte.items():
#         for j, word in enumerate(words):
#             hist[j + 1].append(word)

#     for i, words in hist.items():
#         hist[i] = Counter(words).most_common()

#     logger.info(f"histogramme des positions : {len(hist)} positions (longueur de la plus longue carte)")
#     return hist


# # TODO : fusionner les deux méthodes
# def compute_weighted_histogram_bag(carte, weights=None):
#     """Pour chaque mot, donne son poids comme étant la somme pondérées des positions où il apparait, soit pi(mot) le nombre de fois où mot apparait en position i
#     p(mot) = a1*p1(mot) + a2*p2(mot) + ... + an*pn(mot)
#     """
#     logger.debug(f"compute_weighted_histogram_bag({len(carte)})")

#     # par défaut, des poids de 1 à toutes les positions
#     # fait alors exactement la me chose que compute_histogram_pos
#     if weights is None:
#         weights = defaultdict(lambda: 1)
#     weighted_hist = defaultdict(float)

#     # on ne garde que la seconde composante et on fait +1
#     # pour commencer les index de position à 1 et pas 0
#     second = lambda x: x[1] + 1
#     cog_map_idx = {
#         word: list(map(second, positions)) for word, positions in pivot_cog_map(carte, with_pos=True).items()
#     }

#     for word, positions in cog_map_idx.items():
#         # logger.debug(f"{word} : {positions}")
#         weighted_hist[word] = sum(map(lambda pos: weights[pos], positions))

#     logger.info(f"histogramme pondéré par la position: {len(weighted_hist)} mots différents dans les cartes")
#     return weighted_hist


# def write_histogram_bag(hist, filename, weighted_hist=None):
#     """Sauvegarde la liste des mots énoncés et leur nombre d'occurences (le produit de compute_histogram_bag) au format csv"""
#     logger.debug(f"write_histogram_bag({len(hist)}, {filename}, {weighted_hist is None})")
#     header = ["mot", "nb_occurrences"]
#     if weighted_hist is not None:
#         header.append("occurences_ponderees")
#     with open(filename, "w", newline="", encoding="utf-8") as csvfile:
#         writer = csv.writer(csvfile, **CSV_PARAMS)
#         writer.writerow(header)
#         for (word, nb_ooc) in hist:
#             if weighted_hist is None:
#                 writer.writerow((word, nb_ooc))
#             else:
#                 writer.writerow((word, nb_ooc, round(weighted_hist[word], 2)))
#     logger.info(f"histogramme du sac de mots : {filename}")


# def write_histogram_pos(hist, filename):
#     """Sauvegarde pour chaque position, la liste des mots énoncés et leur nombre d'occurences (le produit de compute_histogram_pos) au format csv"""
#     logger.debug(f"write_histogram_pos({len(hist)}, {filename})")
#     with open(filename, "w", newline="", encoding="utf-8") as csvfile:
#         writer = csv.writer(csvfile, **CSV_PARAMS)
#         header = [f"{k} {i}" for i, k in product(hist.keys(), ["mot", "nb"])]
#         writer.writerow(header)
#         content = zip_longest(*hist.values(), fillvalue=("", ""))
#         for row in content:
#             writer.writerow([x for pair in row for x in pair])
#     logger.info(f"histogramme des positions : {filename}")


# def get_ontology(filename):
#     """Charge l'ontologie (concept, mot énoncé) dans un dico énoncé -> mère"""
#     logger.debug(f"get_ontology({filename})")
#     ontology = defaultdict(lambda: DEFAULT_CONCEPT)

#     with open(filename, encoding="utf-8") as csvfile:
#         reader = csv.reader(csvfile, **CSV_PARAMS)
#         for row in reader:
#             ontology[clean(row[1])] = clean(row[0])
#     logger.info(f"ontologie : {len(ontology.keys())} mots énoncés et {len(set(ontology.values()))} concepts")
#     return ontology


# def apply_ontology(carte, ontology, *, with_unknown=True):
#     """Remplace tous les mots énoncés d'une carte par leur concept mère de l'ontologie"""
#     logger.debug(
#         f"apply_ontology({len(carte)} cartes, {len(ontology)} concepts thesaurus avec inconnus={with_unknown})"
#     )
#     carte_mere = {}
#     unknown_report = defaultdict(list)
#     for k, words in carte.items():
#         carte_mere[k] = [clean(ontology[word]) for word in words if (ontology[word] != DEFAULT_CONCEPT or with_unknown)]
#         for word in words:
#             if ontology[word] == DEFAULT_CONCEPT:
#                 unknown_report[clean(word)].append(k)
#     logger.info(
#         f"calcul de {len(carte_mere)} cartes mères : {sum(len(l) for l in carte_mere.values())} mots au total ({'avec' if with_unknown else 'sans'} mots inconnus)"
#     )
#     logger.info(
#         f"{len(unknown_report)} mots inconnus ({DEFAULT_CONCEPT}) présents dans au total {sum(len(l) for l in unknown_report.values())} cartes"
#     )

#     return carte_mere, unknown_report


# def create_filename(outdir, base, suffix):
#     """Génère un nom de fichier standardisé pour les résultats de calcul"""
#     res = Path(outdir) / Path(f"{Path(base).stem}_{suffix}.csv")
#     return res


# def generate_results(output_dir, cartes_filename, ontologie_filename, with_unknown=False):
#     """"programme principal utilisé par la CLI et la GUI"""
#     logger.debug(f"output = {output_dir}")
#     logger.debug(f"cartes_cognitives = {cartes_filename}")
#     logger.debug(f"ontologie = {ontologie_filename}")
#     logger.debug(f"with_unknown = {with_unknown}")

#     # crée le dossier de sortie si besoin
#     Path(output_dir).mkdir(parents=True, exist_ok=True)
#     # application partielle qui génère un préfixe de nom
#     get_name = partial(create_filename, output_dir, cartes_filename)

#     # chargement des entrées
#     carte = get_cog_maps(cartes_filename)
#     ontology = get_ontology(ontologie_filename)
#     weights = get_weights(WEIGHTED_POSITIONS)
#     weighted_bag = compute_weighted_histogram_bag(carte, weights)
#     # stats "sac de mot" et "position" de la carte
#     write_histogram_bag(compute_histogram_bag(carte), get_name("base_occurences"), weighted_bag)
#     write_histogram_pos(compute_histogram_pos(carte), get_name("base_positions"))

#     # les cartes mères : les cartes dont on a remplacé les mots par les mots mères
#     carte_mere, inconnus = apply_ontology(carte, ontology, with_unknown=with_unknown)
#     write_carte(carte_mere, get_name("meres"))
#     # le report des mots qui n'ont pas de concepts
#     write_carte(inconnus, get_name("inconnus"))

#     weighted_bag = compute_weighted_histogram_bag(carte_mere, weights)
#     write_histogram_bag(compute_histogram_bag(carte_mere), get_name("meres_occurences"), weighted_bag)
#     write_histogram_pos(compute_histogram_pos(carte_mere), get_name("meres_positions"))

#     # les matrices de co-occurences
#     write_cooc_matrix(compute_cooc_matrix(carte), get_name("base_matrice_cooccurences"))
#     write_cooc_matrix(compute_cooc_matrix(carte_mere), get_name("meres_matrice_cooccurences"))


# # %%
# if __name__ == "__main__":
#     carte_mine = get_cog_maps("input/cartes_cog_small.csv")
#     ontology_mine = get_ontology(THESAURUS_LA_MINE)
#     carte_mine_mere, report_inconnu = apply_ontology(carte_mine, ontology_mine, with_unknown=False)
#     # pprint(carte_mine_mere)
#     # pivot_bag = pivot_cog_map(carte_mine_mere, with_pos=False)
#     # pivot_pos = pivot_cog_map(carte_mine_mere, with_pos=True)

#     coocs = compute_cooc_matrix(carte_mine, min_cooc_threshold=2, max_window_width=1)
#     # pprint(coocs)

#     # write_cooc_matrix(coocs, "output/matrix.csv")
#     # pd.DataFrame.from_dict(compute_cooc_matrix(pivot_bag))

#     given_weights = get_weights(WEIGHTED_POSITIONS)
#     weighted_hist_pos = compute_weighted_histogram_bag(carte_mine, given_weights)
#     # pprint(weighted_hist_pos)
#     write_histogram_bag(compute_histogram_bag(carte_mine), "test.csv", weighted_hist_pos)

#     generate_results(OUTPUT_DIR, CARTES_COG_LA_MINE, THESAURUS_LA_MINE)
#     # generate_results(OUTPUT_DIR, CARTES_COG_MINE_FUTUR, THESAURUS_MINE_FUTUR)
