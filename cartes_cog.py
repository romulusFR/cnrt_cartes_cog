# pylint: disable = logging-fstring-interpolation, line-too-long, unused-import
"""Outil de traitement des cartes cognitives"""

__author__ = "Romuald Thion"

# %%

import csv
import logging
from typing import Union, Tuple, Iterator, Optional
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


INPUT_DIR = Path("./input")
CARTES_COG_LA_MINE = INPUT_DIR / "cartes_cog_la_mine.csv"
THESAURUS_LA_MINE = INPUT_DIR / "thesaurus_la_mine.csv"
CARTES_COG_MINE_FUTUR = INPUT_DIR / "cartes_cog_mine_futur.csv"
THESAURUS_MINE_FUTUR = INPUT_DIR / "thesaurus_mine_futur.csv"
WEIGHTED_POSITIONS = INPUT_DIR / "coefficients.csv"
OUTPUT_DIR = "output"
DEFAULT_CONCEPT = "__inconnu__"


CSV_PARAMS = {"delimiter": ";", "quotechar": '"'}
ENCODING = "utf-8"

# typing
StringOrPath = Union[Path, str]
Word = str
Ident = int
Position = int
CogMapsType = dict[Ident, list[Word]]
WeightsType = dict[Position, float]
ThesaurusType = dict[Word, Word]
IndexType = dict[Word, list[Tuple[Ident, Position]]]
OccurrencesType = dict[Word, float]
OccurrencesInPositionsType = dict[Position, Counter[Word]]
MatrixType = dict[Word, dict[Word, float]]


class CogMaps:  # pylint: disable=too-many-instance-attributes
    """Conteneur pour un ensemble de cartes cognitives"""

    # listes des mots considérés comme vides et exlcus de la carte
    EMPTY_WORDS = ("NULL", "")

    @staticmethod
    def clean_word(string: str) -> str:
        """Standarisation du nettoyage des chaines"""
        return string.strip().lower()

    @staticmethod
    def load_cog_maps(filename: StringOrPath) -> CogMapsType:
        """Charge les cartes brutes depuis le fichier CSV"""
        logger.debug(f"CogMaps.load_cog_maps({filename})")

        cog_maps = {}
        with open(filename, encoding=ENCODING) as csvfile:
            reader = csv.reader(csvfile, **CSV_PARAMS)
            for row in reader:
                # indice 0 : l'id de la carte
                # indices 1 et suivants : les mots de la carte
                identifier = int(row[0])
                # on élimine les mots vides et NULL
                cog_maps[identifier] = [CogMaps.clean_word(w) for w in row[1:] if w not in CogMaps.EMPTY_WORDS]

        logger.info(
            f"CogMaps.load_cog_maps: {len(cog_maps)} maps with {sum(len(l) for l in cog_maps.values())} words in total"
        )
        return cog_maps

    @staticmethod
    def load_weights(filename: StringOrPath) -> WeightsType:
        """Charge les poids depuis le fichier CSV"""
        logger.debug(f"CogMaps.load_weights({filename})")
        weights = defaultdict(float)
        with open(filename, encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, **CSV_PARAMS)
            # skip first line
            _ = next(reader)
            for row in reader:
                weights[int(row[0])] = float(row[1])
        return weights

    @staticmethod
    def load_thesaurus(filename: StringOrPath) -> ThesaurusType:
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
        logger.info(f"CogMaps.load_thesaurus: {len(thesaurus.keys())} words to {len(set(thesaurus.values()))} concepts")
        return thesaurus

    def __init__(self, cog_maps_filename=None, thesaurus_filename=None):
        # le fichier duquel lire les cartes cognitives
        self.__cog_maps_filename: Optional[StringOrPath] = None
        # le fichier duquel lire le thesauruse associé
        self.__thesaurus_filename: Optional[StringOrPath] = None
        # les cartes elles-mêmes : à un id, la liste des mots
        self.__cog_maps: CogMapsType = {}
        # le thesaurus
        self.__thesaurus: ThesaurusType = {}
        # l'index inverse : à un mot, la liste des positions (id_ligne, pos_dans_la ligne) où il apparait
        self.__index: Optional[IndexType] = None
        # les poids des positions par défaut : tout le monde à 1
        self.__weights: WeightsType = defaultdict(lambda: 1)
        # le nombre d'occurences, pondérées par weights
        self.__occurrences: Optional[OccurrencesType] = None
        # dans chaque positions, le nombre d'occurences de chaque mot
        self.__occurrences_in_positions: Optional[OccurrencesInPositionsType] = None
        # la matrice de co-occurrences pondérée par weights
        self.__matrix: Optional[MatrixType] = None
        # pour une carte dérivée, sa carte parente
        self.__parent: Optional[CogMaps] = None

        if cog_maps_filename is not None:
            self.__cog_maps_filename = cog_maps_filename
            self.__cog_maps = CogMaps.load_cog_maps(cog_maps_filename)

        if thesaurus_filename is not None:
            self.__thesaurus_filename = thesaurus_filename
            self.__thesaurus = CogMaps.load_thesaurus(thesaurus_filename)

    def invalidate(self) -> None:
        """Invalide les attributs privés qui dependent de cog_maps"""
        self.__index = None
        self.__occurrences_in_positions = None
        self.__occurrences = None
        self.__matrix = None

    def __len__(self) -> int:
        return len(self.__cog_maps)

    def __repr__(self) -> str:
        if self.__parent:
            msg = f"<CogMaps at {hex(id(self))} of length {len(self)} from parent {self.__parent}>"
        else:
            msg = f"<CogMaps at {hex(id(self))} of length {len(self)} from '{self.__cog_maps_filename}' with thesaurus '{self.__thesaurus_filename}'>"
        return msg

    @property
    def cog_maps(self) -> CogMapsType:
        """Les cartes elles mêmes"""
        return self.__cog_maps

    @cog_maps.setter
    def cog_maps(self, values: CogMapsType) -> None:
        """On bloque l'affectation sur cog_maps"""
        if not isinstance(values, dict):
            raise TypeError(f"CogMaps.cog_maps does not support direct assignment from {type(values)}")
        self.__cog_maps = values
        self.invalidate()

    @property
    def thesaurus(self) -> ThesaurusType:
        """Le thesaurus"""
        return self.__thesaurus

    @thesaurus.setter
    def thesaurus(self, _) -> None:  # pylint: disable=no-self-use
        """On bloque l'affectation sur thesaurus"""
        raise TypeError("CogMaps.thesaurus does not support direct assignment")

    def dump(self, filename: StringOrPath) -> None:
        """Ecrit les cartes dans un fichier"""
        logger.debug(f"CogMaps.dump({len(self)}, {filename})")
        with open(filename, "w", newline="", encoding=ENCODING) as csvfile:
            writer = csv.writer(csvfile, **CSV_PARAMS)
            for i, words in self.__cog_maps.items():
                writer.writerow([i] + words)  # type: ignore
        logger.info(f"CogMaps.dump to {filename}")

    @property
    def index(self) -> IndexType:
        """Index "pivot" des cartes : pour chaque mot, donne les couples (id, pos) des cartes où il apparait"""
        if self.__index is None:
            logger.debug(f"CogMaps.create_index({len(self)})")
            self.__index = defaultdict(list)
            for identifier, words in self.__cog_maps.items():
                for pos, word in enumerate(words):
                    # NOTE : on fait commencer les positions à 1
                    value = (identifier, pos + 1)
                    self.__index[word].append(value)
        return self.__index

    @index.setter
    def index(self, _) -> None:  # pylint: disable=no-self-use
        """On bloque l'affectation sur index"""
        raise TypeError("CogMaps.index does not support direct assignment")

    @property
    def words(self) -> Iterator[Word]:
        """L'ensemble des mots énoncés dans les cartes"""
        return iter(self.index.keys())

    @property
    def weights(self) -> WeightsType:
        """Les poids de chaque positions"""
        return self.__weights

    @weights.setter
    def weights(self, values: WeightsType):
        # dispatch manuel
        if not isinstance(values, dict):
            raise NotImplementedError(f"CogMaps.weights cannot dispatch {type(values)}")
        # ràz des occurences et de la matrice des co-occurences
        self.__occurrences = None
        self.__matrix = None
        self.__weights = values

    @property
    def occurrences(self) -> OccurrencesType:
        """Pour chaque mot, donne son poids comme étant la somme pondérées des positions où il apparait, soit pi(mot) le nombre de fois où mot apparait en position i
        p(mot) = a1*p1(mot) + a2*p2(mot) + ... + an*pn(mot)
        """

        if self.__occurrences is None:
            logger.debug(f"CogMaps.occurrences({len(self.__cog_maps)}, {self.__weights})")
            self.__occurrences = defaultdict(float)
            # on ne garde que la seconde composante de l'index
            second = lambda x: x[1]
            position_index = {word: list(map(second, positions)) for word, positions in self.index.items()}

            for word, positions in position_index.items():
                self.__occurrences[word] = sum(map(lambda pos: self.weights[pos], positions))

        return self.__occurrences

    @occurrences.setter
    def occurrences(self, _) -> None:  # pylint: disable=no-self-use
        """On bloque l'affectation sur occurrences"""
        raise TypeError("CogMaps.occurrences does not support direct assignment")

    def dump_occurrences(self, filename: StringOrPath) -> None:
        """Sauvegarde la liste des mots énoncés et leur nombre d'occurrences (le produit de compute_histogram_bag) au format csv"""
        logger.debug(f"CogMaps.dump_occurrences({len(self.cog_maps)}, {filename})")
        header = ["mot", "nb_occurrences", "occurences_ponderees"]

        with open(filename, "w", newline="", encoding=ENCODING) as csvfile:
            writer = csv.writer(csvfile, **CSV_PARAMS)
            writer.writerow(header)
            for word in sorted(self.words):
                writer.writerow((word, len(self.index[word]), round(self.occurrences[word], 2)))
        logger.info(f"CogMaps.dump_occurrences to {filename}")

    @property
    def occurrences_in_position(self) -> OccurrencesInPositionsType:
        """Pour chaque position, calcule le nombre d'occurence de chaque mot dans cette position"""

        if self.__occurrences_in_positions is None:
            logger.debug(f"CogMaps.occurrences_in_position({len(self)})")
            words_in_pos = defaultdict(list)

            for word, positions in self.index.items():
                for (_, position) in positions:
                    words_in_pos[position].append(word)

            self.__occurrences_in_positions = {position: Counter(words) for (position, words) in words_in_pos.items()}
            logger.info(
                f"CogMaps.occurrences_in_position: {len(self.__occurrences_in_positions)} positions (longest map)"
            )
        return self.__occurrences_in_positions

    def dump_occurrences_in_position(self, filename: StringOrPath):
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
        logger.info(f"CogMaps.dump_occurrences_in_position to {filename}")

    def apply(self, *, with_unknown=True):
        """Remplace tous les mots énoncés d'une carte par leur concept mère de l'ontologie"""
        logger.debug(
            f"CogMaps.apply({len(self)} maps, {len(self.__thesaurus)} concepts thesaurus with unknowns={with_unknown})"
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
            f"CogMaps.apply: {len(concept_maps)} concept maps with {sum(len(l) for l in concept_maps.values())} words ({'with' if with_unknown else 'without'} unknown words)"
        )
        logger.info(
            f"CogMaps.apply: {len(unknown_report)} unknown words ({DEFAULT_CONCEPT}) in {sum(len(l) for l in unknown_report.values())} maps"
        )

        new_cog_maps = CogMaps()
        # on définit les cartes
        new_cog_maps.__cog_maps = concept_maps  # pylint: disable=protected-access
        # le parent
        new_cog_maps.__parent = self  # pylint: disable=protected-access
        # on reprend la même carte de poids
        new_cog_maps.__weights = self.__weights.copy()  # pylint: disable=protected-access

        # on utilise le fait que le rapport des unknnows est une cog_maps aussi
        unknowns_maps = CogMaps()
        unknowns_maps.cog_maps = unknown_report
        unknowns_maps.__parent = self  # pylint: disable=protected-access
        return new_cog_maps, unknowns_maps

    @property
    def matrix(self) -> MatrixType:
        """Calcule la matrice de co-occurrences des mots d'une carte

        produit un dictionnaire des co-occurrences :
        qui à chaque mot ligne
           -> un dictionnaire qui à chaque mot colonne
               -> le nombre de cartes où on apparait en commun

        en jouant avec l'attribut self.weight, on peut obtenir différentes
        pondération de la distance inter-mots
        """
        if self.__matrix is None:
            self.__matrix = defaultdict(lambda: defaultdict(float))  # type: ignore
            for word_row in self.index:
                for word_col in self.index:
                    # toutes les paires de paires (id_row, pos_row), (id_col, pos_col)
                    pos_prod = product(self.index[word_row], self.index[word_col])
                    # si on est ensemble dans la même carte
                    # alors on calcule l'écart absolu des positions
                    deltas = [
                        abs(row_pair[1] - col_pair[1])
                        for (row_pair, col_pair) in pos_prod
                        if row_pair[0] == col_pair[0]
                    ]

                    # sur les écarts de positions au sein des mêmes cartes, on va
                    # utiliser les poids positionnels, mais sur des écarts
                    # si l'écart ets de 0, on mets un poids de 1.0
                    self.__matrix[word_row][word_col] = sum(self.weights.get(delta, 0.0) if delta else 1.0 for delta in deltas)
        return self.__matrix

    def dump_matrix(self, filename: StringOrPath) -> None:
        """Ecrit les cartes depuis le dict/dic python"""
        logger.debug(f"CogMaps.dump_matrix({len(self.matrix)}, {filename})")
        words = sorted(self.words)
        with open(filename, "w", newline="", encoding=ENCODING) as csvfile:
            writer = csv.writer(csvfile, **CSV_PARAMS)
            writer.writerow(["/"] + words)
            for row_word in words:
                writer.writerow([row_word] + [str(round(self.matrix[row_word][col_word], 2)) for col_word in words])
        logger.info(f"CogMaps.dump_matrix: {filename}")


# %%
def gen_filename(outdir: StringOrPath, base: StringOrPath, suffix: str) -> Path:
    """Outil : Génère un nom de fichier standardisé pour les résultats de calcul"""
    return Path(outdir) / Path(f"{Path(base).stem}_{suffix}.csv")


def generate_results(
    output_dir: StringOrPath,
    cog_maps_filename: StringOrPath,
    thesaurus_filename: StringOrPath,
    with_unknown: bool = False,
) -> None:
    """"Wrapper principal utilisé par la CLI et la GUI"""
    logger.debug(f"output_dir = {output_dir}")
    logger.debug(f"cog_maps__filename = {cog_maps_filename}")
    logger.debug(f"thesaurus_filename = {thesaurus_filename}")
    logger.debug(f"with_unknown = {with_unknown}")

    # crée le dossier de sortie si besoin
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    # application partielle qui génère un préfixe de nom
    get_name = partial(gen_filename, output_dir, cog_maps_filename)

    # chargement des entrées
    the_cog_maps = CogMaps(cog_maps_filename, thesaurus_filename)
    the_cog_maps.weights = CogMaps.load_weights(WEIGHTED_POSITIONS)
    the_cog_maps.dump(get_name("base"))
    the_cog_maps.dump_occurrences(get_name("base_occurrences"))
    the_cog_maps.dump_occurrences_in_position(get_name("base_positions"))
    the_cog_maps.dump_matrix(get_name("base_matrice"))

    # les cartes mères : les cartes dont on a remplacé les mots par les mots mères
    the_concept_maps, the_unknowns_maps = the_cog_maps.apply(with_unknown=with_unknown)
    the_concept_maps.dump(get_name("meres"))
    the_concept_maps.dump_occurrences(get_name("meres_occurrences"))
    the_concept_maps.dump_occurrences_in_position(get_name("meres_positions"))
    the_concept_maps.dump_matrix(get_name("meres_matrice"))

    # le rapport des mots qui n'ont pas de concepts
    the_unknowns_maps.dump(get_name("inconnus"))


if __name__ == "__main__":
    WITH_UNKNOWNS = False
    generate_results(OUTPUT_DIR, CARTES_COG_LA_MINE, THESAURUS_LA_MINE, with_unknown=WITH_UNKNOWNS)
    generate_results(OUTPUT_DIR, CARTES_COG_MINE_FUTUR, THESAURUS_MINE_FUTUR, with_unknown=WITH_UNKNOWNS)

    # mes_cartes = CogMaps(Path("input/cartes_cog_small.csv"))
    # mes_cartes.dump_occurrences("test1.csv")
    # mes_cartes.weights = CogMaps.load_weights("input/coefficients.csv")
    # mes_cartes.dump_occurrences("test2.csv")
    # mes_cartes.dump_occurrences_in_position("test3.csv")

    # mes_cartes = CogMaps(Path("input/cartes_cog_small.csv"), THESAURUS_LA_MINE)
    # mes_cartes.weights = CogMaps.load_weights("input/coefficients.csv")
    # mes_cartes_meres, mes_inconnus = mes_cartes.apply(with_unknown=False)
    # mes_cartes_meres.dump_matrix("test.csv")
    # mes_cartes_meres.dump("meres.csv")
