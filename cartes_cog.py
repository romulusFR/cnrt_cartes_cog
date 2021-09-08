# pylint: disable = logging-fstring-interpolation, line-too-long, unused-import
"""Outil de traitement des cartes cognitives"""

__author__ = "Romuald Thion"

# %%

import csv
import logging
from typing import Union, Tuple, Iterator
from collections import Counter, defaultdict
from itertools import product, zip_longest
from functools import partial, singledispatchmethod
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

    @staticmethod
    def clean_word(string: str):
        """Standarisation du nettoyage des chaines"""
        return string.strip().lower()

    @staticmethod
    def load_weights(filename):
        """Charge les poids depuis le fichier CSV"""
        logger.debug(f"CogMap.load_weights({filename})")
        weights = defaultdict(float)
        with open(filename, encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, **CSV_PARAMS)
            # skip first line
            _ = next(reader)
            for row in reader:
                weights[int(row[0])] = float(row[1])
        return weights

    @staticmethod
    def load_cog_maps(filename: Union[Path, str]):
        """Charge les cartes brutes depuis le fichier CSV"""
        logger.debug(f"CogMap.load_cog_maps({filename})")

        cog_maps = {}
        with open(filename, encoding=ENCODING) as csvfile:
            reader = csv.reader(csvfile, **CSV_PARAMS)
            for row in reader:
                # indice 0 : l'id de la carte
                # indices 1 et suivants : les mots de la carte
                identifier = int(row[0])
                # on élimine les mots vides et NULL
                cog_maps[identifier] = [CogMaps.clean_word(w) for w in row[1:] if w not in CogMaps.EMPTY_WORDS]

        logger.info(f"CogMap.load: {len(cog_maps)} maps with {sum(len(l) for l in cog_maps.values())} total words")
        return cog_maps

    def __init__(self, cog_maps_filename=None, thesaurus_filename=None):
        # le fichier duquel lire les cartes cognitives
        self.__cog_maps_filename = None
        # le fichier duquel lire le thesauruse associé
        self.__thesaurus_filename = None
        # les cartes elles-mêmes : à un id, la liste des mots
        self.__cog_maps: dict[int, list[str]] = {}
        # l'index inverse : à un mot, la liste des positions (id_ligne, pos_dans_la ligne) où il apparait
        self.__index = None
        # les poids des positions par défaut : tout le monde à 1
        self.__weights = defaultdict(lambda: 1)
        # le nombre d'occurences, pondérées par weights
        self.__occurrences = None
        # dans chaque positions, le nombre d'occurences de chaque mot
        self.__occurrences_in_positions = None
        # pour une carte dérivée, sa carte parente
        self.__parent = None

        if cog_maps_filename is not None:
            self.__cog_maps_filename = cog_maps_filename
            self.__cog_maps = CogMaps.load_cog_maps(cog_maps_filename)

        if thesaurus_filename is not None:
            self.__thesaurus_filename = thesaurus_filename
            self.__thesaurus = CogMaps.load_thesaurus(thesaurus_filename)

    def invalidate(self):
        self.__index = None
        self.__occurrences = None
        self.__occurrences_in_positions = None

    def __len__(self):
        return len(self.__cog_maps)

    def __repr__(self) -> str:
        return f"<CogMaps at {hex(id(self))} of length {len(self)} from '{self.__cog_maps_filename}'>"

    @property
    def cog_maps(self):
        """Les cartes elles mêmes"""
        return self.__cog_maps

    @cog_maps.setter
    def cog_maps(self, _):  # pylint: disable=no-self-use
        """On bloque l'affectation sur cog_maps"""
        raise TypeError("CogMap.cog_maps does not support direct assignment")

    def dump(self, filename: Union[Path, str]):
        """Ecrit les cartes dans un fichier"""
        logger.debug(f"CogMap.dump({len(self)}, {filename})")
        with open(filename, "w", newline="", encoding=ENCODING) as csvfile:
            writer = csv.writer(csvfile, **CSV_PARAMS)
            for i, words in self.__cog_maps.items():
                writer.writerow([i] + words)  # type: ignore
        logger.info(f"CogMap.dump to {filename}")
        return self

    @property
    def index(self) -> dict[str, list[Tuple[int, int]]]:
        """Index "pivot" des cartes : pour chaque mot, donne les couples (id, pos) des cartes où il apparait"""
        if self.__index is None:
            logger.debug(f"CogMap.create_index({len(self)})")
            self.__index = defaultdict(list)
            for identifier, words in self.__cog_maps.items():
                for pos, word in enumerate(words):
                    # NOTE : on fait commencer les positions à 1
                    value = (identifier, pos + 1)
                    self.__index[word].append(value)
        return self.__index

    @index.setter
    def index(self, _):  # pylint: disable=no-self-use
        """On bloque l'affectation sur index"""
        raise TypeError("CogMap.index does not support direct assignment")

    @property
    def words(self) -> Iterator[str]:
        """L'ensemble des mots énoncés dans les cartes"""
        return iter(self.index.keys())

    @property
    def weights(self) -> dict[int, float]:
        """Les poids de chaque positions"""
        return self.__weights

    @weights.setter
    def weights(self, values):
        # dispatch manuel
        if not isinstance(values, dict):
            raise NotImplementedError(f"CogMaps.weights cannot dispatch {type(values)}")
        # ràz des occurences
        self.__occurrences = None
        self.__weights = values

    @property
    def occurrences(self):
        """Pour chaque mot, donne son poids comme étant la somme pondérées des positions où il apparait, soit pi(mot) le nombre de fois où mot apparait en position i
        p(mot) = a1*p1(mot) + a2*p2(mot) + ... + an*pn(mot)
        """

        if self.__occurrences is None:
            logger.debug(f"CogMap.occurrences({len(self.__cog_maps)}, {self.__weights})")
            self.__occurrences = defaultdict(float)
            # on ne garde que la seconde composante de l'index
            second = lambda x: x[1]
            position_index = {word: list(map(second, positions)) for word, positions in self.index.items()}

            for word, positions in position_index.items():
                self.__occurrences[word] = sum(map(lambda pos: self.weights[pos], positions))

        return self.__occurrences

    def dump_occurrences(self, filename):
        """Sauvegarde la liste des mots énoncés et leur nombre d'occurrences (le produit de compute_histogram_bag) au format csv"""
        logger.debug(f"CogMap.dump_occurrences({len(self.cog_maps)}, {filename})")
        header = ["mot", "nb_occurrences", "occurences_ponderees"]

        with open(filename, "w", newline="", encoding=ENCODING) as csvfile:
            writer = csv.writer(csvfile, **CSV_PARAMS)
            writer.writerow(header)
            for word in sorted(self.words):
                writer.writerow((word, len(self.index[word]), round(self.occurrences[word], 2)))
        logger.info(f"CogMap.dump_occurrences to {filename}")

    @property
    def occurrences_in_position(self):
        """Pour chaque position, calcule le nombre d'occurence de chaque mot dans cette position"""

        if self.__occurrences_in_positions is None:
            logger.debug(f"CogMaps.occurrences_in_position({len(self)})")
            words_in_pos = defaultdict(list)

            for word, positions in self.index.items():
                for (_, position) in positions:
                    words_in_pos[position].append(word)

            self.__occurrences_in_positions = {position: Counter(words) for (position, words) in words_in_pos.items()}
            logger.info(
                f"histogramme des positions : {len(self.__occurrences_in_positions)} positions (longueur de la plus longue carte)"
            )
        return self.__occurrences_in_positions

    def dump_occurrences_in_position(self, filename):
        """Sauvegarde pour chaque position, la liste des mots énoncés et leur nombre d'occurences (le produit de compute_histogram_pos) au format csv"""
        logger.debug(f"CogMaps.dump_occurrences_in_position({len(self)}, {filename})")
        positions = sorted(self.occurrences_in_position.keys())
        hist = {position: self.occurrences_in_position[position].most_common() for position in positions}
        with open(filename, "w", newline="", encoding=ENCODING) as csvfile:
            writer = csv.writer(csvfile, **CSV_PARAMS)
            header = [f"{k} {i}" for i, k in product(hist.keys(), ["mot", "nb"])]
            writer.writerow(header)
            content = zip_longest(*hist.values(), fillvalue=("", ""))
            for row in content:
                writer.writerow([x for pair in row for x in pair])
        logger.info(f"histogramme des positions : {filename}")

    @staticmethod
    def load_thesaurus(filename):
        """Charge l'ontologie (concept, mot énoncé) dans un dico "mot énoncé" -> "mot mère"

        Assure l'application de CogMaps.clean_word"""
        logger.debug(f"CogMaps.load_thesaurus({filename})")
        thesaurus = defaultdict(lambda: DEFAULT_CONCEPT)

        with open(filename, encoding=ENCODING) as csvfile:
            reader = csv.reader(csvfile, **CSV_PARAMS)
            for row in reader:
                word = CogMaps.clean_word(row[1])
                concept = CogMaps.clean_word(row[0])
                if word not in CogMaps.EMPTY_WORDS and concept not in CogMaps.EMPTY_WORDS:
                    thesaurus[word] = concept
        logger.info(f"Thesaurus : {len(thesaurus.keys())} words and {len(set(thesaurus.values()))} concepts")
        return thesaurus

    def apply(self, *, with_unknown=True):
        """Remplace tous les mots énoncés d'une carte par leur concept mère de l'ontologie"""
        logger.debug(
            f"CogMaps.apply({len(self)} cartes, {len(self.__thesaurus)} concepts thesaurus avec inconnus={with_unknown})"
        )
        concept_maps = {}
        unknown_report = defaultdict(list)
        for k, words in self.__cog_maps.items():
            concept_maps[k] = [
                self.__thesaurus[word] for word in words if (self.__thesaurus[word] != DEFAULT_CONCEPT or with_unknown)
            ]
            for word in words:
                if self.__thesaurus[word] == DEFAULT_CONCEPT:
                    unknown_report[word].append(k)
        logger.info(
            f"calcul de {len(concept_maps)} cartes mères : {sum(len(l) for l in concept_maps.values())} mots au total ({'avec' if with_unknown else 'sans'} mots inconnus)"
        )
        logger.info(
            f"{len(unknown_report)} mots inconnus ({DEFAULT_CONCEPT}) présents dans au total {sum(len(l) for l in unknown_report.values())} cartes"
        )

        new_cog_maps = CogMaps()
        new_cog_maps.__cog_maps = concept_maps # pylint: disable=protected-access
        new_cog_maps.__parent = self # pylint: disable=protected-access
        return new_cog_maps, unknown_report


def gen_filename(outdir, base, suffix):
    """Génère un nom de fichier standardisé pour les résultats de calcul"""
    return Path(outdir) / Path(f"{Path(base).stem}_{suffix}.csv")


# %%

if __name__ == "__main__":
    # mes_cartes = CogMaps(Path("input/cartes_cog_small.csv"))
    # mes_cartes.dump_occurrences("test1.csv")
    # mes_cartes.weights = CogMaps.load_weights("input/coefficients.csv")
    # mes_cartes.dump_occurrences("test2.csv")
    # mes_cartes.dump_occurrences_in_position("test3.csv")


    mes_cartes = CogMaps(Path("input/cartes_cog_small.csv"), THESAURUS_LA_MINE)

# def get_weights(filename):


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
