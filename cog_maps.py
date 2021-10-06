# pylint: disable = logging-fstring-interpolation, line-too-long, unused-import
"""Module principal de chargement, traitement et export des cartes cognitives"""

__author__ = "Romuald Thion"

# %%
import locale
import csv
import logging
import time
from math import exp
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

locale.setlocale(locale.LC_ALL, "")


# typing
StringOrPath = Union[Path, str]
Word = str
Ident = int
Position = int
Level = str
CogMapsType = dict[Ident, list[Word]]
WeightsType = dict[Position, float]
WeightsMapType = dict[str, WeightsType]
ThesaurusType = dict[Word, Word]
ThesaurusMapType = dict[Level, ThesaurusType]
IndexType = dict[Word, list[Tuple[Ident, Position]]]
OccurrencesType = dict[Word, float]
OccurrencesInPositionsType = dict[Position, Counter[Word]]
MatrixType = dict[Word, dict[Word, float]]


INPUT_DIR = Path("./input")

if not INPUT_DIR.exists():
    logger.error("input directory %s does not exist", INPUT_DIR)
    raise FileNotFoundError(f"input directory {INPUT_DIR} does not exist")

# fichiers par défaut
CM_SMALL_FILENAME = INPUT_DIR / "cartes_cog_small.csv"
CM_LA_MINE_FILENAME = INPUT_DIR / "cartes_cog_la_mine.csv"
CM_FUTUR_FILENAME = INPUT_DIR / "cartes_cog_mine_futur.csv"
THESAURUS_FILENAME = INPUT_DIR / "thesaurus.csv"
WEIGHTS_MAP_FILENAME = INPUT_DIR / "coefficients.csv"
OUTPUT_DIR = Path("output")

# pour les I/O
CSV_PARAMS = {"delimiter": ";", "quotechar": '"'}
ENCODING = "utf-8"

# valeur par défaut
DEFAULT_CONCEPT: Word = "__inconnu__"
DEFAULT_MAX_LEN: int = 15
# BUG éviter ici defaultdict car collision avec le .get(key, 0.0)
DEFAULT_WEIGHTS: WeightsType = {i: 1.0 for i in range(1, DEFAULT_MAX_LEN + 1)}
# TODO corriger : pas clair si nom du précédent
DEFAULT_WEIGHTS_NAME: str = "arithmetique"

# constante pour le thésaurus
BASE_LVL: Level = "base"
CONCEPT_LVL: Level = "concept"
MOTHER_LVL: Level = "mother"
GD_MOTHER_LVL: Level = "gd_mother"
LEVELS = [BASE_LVL, CONCEPT_LVL, MOTHER_LVL, GD_MOTHER_LVL]


class CogMaps:  # pylint: disable=too-many-instance-attributes
    """Conteneur pour un ensemble de cartes cognitives"""

    # listes des mots considérés comme vides et exlcus de la carte
    EMPTY_WORDS = ("null", "")

    @staticmethod
    def clean_word(string: str) -> str:
        """Standarisation du nettoyage des chaines"""
        return string.strip().lower()

    @staticmethod
    def load_cog_maps(filename: StringOrPath, predicate) -> CogMapsType:
        """Charge les cartes brutes depuis le fichier CSV"""
        logger.debug(f"CogMaps.load_cog_maps({filename})")

        cog_maps = {}
        with open(filename, encoding=ENCODING) as csvfile:
            reader = csv.reader(csvfile, **CSV_PARAMS)
            for row in reader:
                # indice 0 : l'id de la carte
                # indices 1 et suivants : les mots de la carte
                identifier = int(row[0])
                # on élimine les mots vides et NULL et on filtre les cartes qui ne respectent pas le prédicat
                if predicate(identifier):
                    cog_maps[identifier] = [
                        CogMaps.clean_word(w) for w in row[1:] if CogMaps.clean_word(w) not in CogMaps.EMPTY_WORDS
                    ]

        logger.info(
            f"CogMaps.load_cog_maps: {len(cog_maps)} maps with {sum(len(l) for l in cog_maps.values())} words in total"
        )
        return cog_maps

    @staticmethod
    def load_weights(filename: StringOrPath) -> WeightsMapType:
        """Charge les poids depuis le fichier CSV"""
        logger.debug(f"CogMaps.load_weights({filename})")
        weights: WeightsMapType = defaultdict(dict)
        with open(filename, encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, **CSV_PARAMS)
            # remember first line for names
            names = next(reader)
            for row in reader:
                position = int(row[0])
                for i, col in enumerate(row[1::], start=1):
                    weights[names[i]][position] = float(col)
        return weights

    @staticmethod
    def load_thesaurus_map(filename: StringOrPath) -> ThesaurusMapType:
        """Charge l'ontologie (concept, mot énoncé) dans un dico "mot énoncé" -> "mot mère"

        Format attendu (sans en-tête):
        0 - Mots énoncés;
        1 - Code mots énoncés;
        2 - Concepts énoncés;       -- clef 0
        3 - Concepts mères;         -- clef 1
        4 - Code Mère;
        5 - Concepts grands-mères;  -- clef 2
        6 - Code Grand-mère

        Assure l'application de CogMaps.clean_word"""
        logger.debug(f"CogMaps.load_thesaurus({filename})")
        # defaultdict(lambda: DEFAULT_CONCEPT)
        thesaurus_map: ThesaurusMapType = {
            CONCEPT_LVL: defaultdict(lambda: DEFAULT_CONCEPT),  # word -> concept
            MOTHER_LVL: defaultdict(lambda: DEFAULT_CONCEPT),  # concept -> mother
            GD_MOTHER_LVL: defaultdict(lambda: DEFAULT_CONCEPT),  # mother -> grand_mother
        }

        def check_and_add(level: Level, src: Word, dst: Word):
            src = CogMaps.clean_word(src)
            dst = CogMaps.clean_word(dst)
            if src not in CogMaps.EMPTY_WORDS and dst not in CogMaps.EMPTY_WORDS:
                if thesaurus_map[level].get(src, dst) != dst:
                    logger.warning(
                        "CogMaps.load_thesaurus at %s: %s -> %s overridden by %s",
                        level,
                        src,
                        thesaurus_map[level][src],
                        dst,
                    )
                thesaurus_map[level][src] = dst
            else:
                logger.warning("CogMaps.load_thesaurus empty mapping %s -> %s", src, dst)

        with open(filename, encoding=ENCODING) as csvfile:
            reader = csv.reader(csvfile, **CSV_PARAMS)
            for row in reader:
                # word = CogMaps.clean_word(row[0])
                # concept = CogMaps.clean_word(row[3])
                if len(row) != 7:
                    logger.warning("CogMaps.load_thesaurus map cannot row %s of len %i", row, len(row))
                [word, _, concept, mother, _, grand_mother, _] = row

                check_and_add(CONCEPT_LVL, word, concept)
                check_and_add(MOTHER_LVL, concept, mother)
                check_and_add(GD_MOTHER_LVL, mother, grand_mother)

        logger.info(f"CogMaps.load_thesaurus: {len(thesaurus_map)} levels")
        # words to {len(set(thesaurus.values()))} concepts")
        return thesaurus_map

    def __init__(self, cog_maps_filename=None, predicate=lambda _ : True):
        # le fichier duquel lire les cartes cognitives
        self.__cog_maps_filename: Optional[StringOrPath] = cog_maps_filename
        # les cartes elles-mêmes : à un id, la liste des mots
        self.__cog_maps: CogMapsType = {}
        # le thesaurus
        self.__thesaurus: ThesaurusType = {}
        # l'index inverse : à un mot, la liste des positions (id_ligne, pos_dans_la ligne) où il apparait
        self.__index: Optional[IndexType] = None
        # les poids des positions par défaut : tout le monde à 1
        self.__weights: WeightsType = DEFAULT_WEIGHTS
        # le nombre d'occurences, pondérées par weights
        self.__occurrences: Optional[OccurrencesType] = None
        # dans chaque positions, le nombre d'occurences de chaque mot
        self.__occurrences_in_positions: Optional[OccurrencesInPositionsType] = None
        # la matrice de co-occurrences pondérée par weights
        self.__matrix: Optional[MatrixType] = None
        # pour une carte dérivée, sa carte parente
        self.__parent: Optional[CogMaps] = None

        if cog_maps_filename is not None:
            self.__cog_maps = CogMaps.load_cog_maps(cog_maps_filename, predicate=predicate)

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
            msg = f"<CogMaps at {hex(id(self))} of length {len(self)} from '{self.__cog_maps_filename}'>"
        return msg

    @property
    def filename(self) -> Optional[StringOrPath]:
        """le nom du fichier utilisé pour la carte"""
        return self.__cog_maps_filename

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
    def thesaurus(self, data: ThesaurusType) -> None:  # pylint: disable=no-self-use
        """On bloque l'affectation sur thesaurus"""
        # raise TypeError("CogMaps.thesaurus does not support direct assignment")
        self.__thesaurus = data

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
            logger.info(f"CogMaps.create_index: {len(self.__index)} different words")
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
            logger.debug(f"CogMaps.occurrences({len(self.__cog_maps)})")  # {self.__weights}
            self.__occurrences = {}
            # on ne garde que la seconde composante de l'index
            second = lambda x: x[1]
            # à chaque mot la liste de ses positions (en oubliant l'id de carte)
            position_index = {word: list(map(second, positions)) for word, positions in self.index.items()}
            # pour chaque mot et ses poitions
            for word, positions in position_index.items():
                # on remplace la position par son poids et on somme
                # on utilise dict.get pour donner un poids par défaut de 0.0
                # aux positions dont le poids n'est pas défini
                self.__occurrences[word] = sum(map(lambda pos: self.weights.get(pos, 0.0), positions))

        return self.__occurrences

    @occurrences.setter
    def occurrences(self, _) -> None:  # pylint: disable=no-self-use
        """On bloque l'affectation sur occurrences"""
        raise TypeError("CogMaps.occurrences does not support direct assignment")

    def dump_occurrences_many(self, filename: StringOrPath, weights_map: WeightsMapType) -> None:
        """Genère les positions pondérées pour une famille de pondérations"""
        header = ["mot", "nb_occurrences", *weights_map.keys()]
        logger.debug("CogMaps.dump_occurences_many: header %s", header)
        occurrences = {}

        for name, weights in weights_map.items():
            self.weights = weights
            occurrences[name] = self.occurrences

        with open(filename, "w", newline="", encoding=ENCODING) as csvfile:
            writer = csv.writer(csvfile, **CSV_PARAMS)
            writer.writerow(header)
            for word in sorted(self.words):
                # ici, affichage avec la locale
                # https://stackoverflow.com/questions/1823058/how-to-print-number-with-commas-as-thousands-separators
                # row = [f"{round(occurrences[name][word], 2):n}" for name in weights_map]
                row = [f"{round(occurrences[name][word], 2)}" for name in weights_map]
                writer.writerow((word, len(self.index[word]), *row))
        logger.info("CogMaps.dump_occurences_many to %s", filename)

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
        # la carte après application du thesaurus
        concept_maps = {}
        # les mots qui n'ont pas d'image
        unknown_report = defaultdict(list)
        # pour chaque carte, on garde son identifiant
        for identifier, words in self.__cog_maps.items():
            # on remplace chacun de ses mots par son image dans le thesaurus
            concept_maps[identifier] = [
                self.__thesaurus[word] for word in words if (self.__thesaurus[word] != DEFAULT_CONCEPT or with_unknown)
            ]
            # on ajoute les mots qui n'ont pas d'image
            for word in words:
                if self.__thesaurus[word] == DEFAULT_CONCEPT:
                    unknown_report[word].append(identifier)

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
        # on utilise le même nom de fichier
        path = Path(self.filename)
        # pylint: disable=protected-access
        new_cog_maps.__cog_maps_filename = f"concepts_of_{path.stem}{path.suffix}"

        # on utilise le fait que le rapport des unknnows est une cog_maps aussi
        unknowns_maps = CogMaps()
        unknowns_maps.cog_maps = unknown_report
        unknowns_maps.__parent = self  # pylint: disable=protected-access
        return new_cog_maps, unknowns_maps

    def apply_many(self, thesaurus_maps, *, with_unknown=True):
        """Génération des 4 niveaux cartes du thesaurus (base, concept, mother, gd_mother) et les 3 rapports d'erreur"""
        logger.debug(f"CogMaps.apply_many({len(self)}, {len(thesaurus_maps)})")
        the_maps = {BASE_LVL: self}
        the_reports = {}
        # le thesaurus a plusieurs niveau. On va appliquer chacun
        for i, level in enumerate(LEVELS[1::]):
            previous_level = LEVELS[i]
            the_maps[previous_level].thesaurus = thesaurus_maps[level]
            the_new_maps, the_unknowns_maps = the_maps[previous_level].apply(with_unknown=with_unknown)
            the_maps[level] = the_new_maps
            the_reports[level] = the_unknowns_maps
            # le rapport des mots qui n'ont pas d'image, on le produit tout de suite

        return the_maps, the_reports

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
            logger.debug(f"CogMaps.matrix({len(self)})")
            start = time.perf_counter_ns()
            self.__matrix = defaultdict(lambda: defaultdict(float))  # type: ignore

            for _, words in self.cog_maps.items():
                pos_prod = product(enumerate(words), enumerate(words))
                for (pos_row, word_row), (pos_col, word_col) in pos_prod:
                    distance = abs(pos_row - pos_col)
                    weigthed_distance = self.weights.get(distance, 0.0) if distance else 1.0
                    self.__matrix[word_row][word_col] += weigthed_distance
            logger.info("CogMaps.matrix: duration %fms", round((time.perf_counter_ns() - start) / 10 ** 6, 2))
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


def gen_filename(outdir: StringOrPath, base: StringOrPath, suffix: str) -> Path:
    """Outil : Génère un nom de fichier standardisé pour les résultats de calcul"""
    # return Path(outdir) / Path(f"{Path(base).stem}_{suffix}.csv")
    return Path(outdir) / f"{Path(base).stem}_{suffix}.csv"


def compose(src: dict, dst: dict):
    """Composition de deux dictionnaires"""
    return {k: dst.get(v, DEFAULT_CONCEPT) for k, v in src.items()}


def generate_results(
    output_dir: StringOrPath,
    cog_maps_filename: StringOrPath,
    thesaurus_filename: StringOrPath,
    weights_filename: StringOrPath,
    with_unknown: bool = False,
    weights_name: str = DEFAULT_WEIGHTS_NAME,
) -> list[Tuple[Level, CogMaps]]:
    """ "Wrapper principal utilisé par la CLI et la GUI"""
    logger.debug(f"output_dir = {output_dir}")
    logger.debug(f"cog_maps_filename = {cog_maps_filename}")
    logger.debug(f"thesaurus_filename = {thesaurus_filename}")
    logger.debug(f"weights_filename = {weights_filename}")
    logger.debug(f"with_unknown = {with_unknown}")

    # crée le dossier de sortie si besoin
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    # application partielle qui génère un préfixe de nom
    get_name = partial(gen_filename, output_dir, cog_maps_filename)
    # constantes
    occurrences_suffix = "occurrences"
    positions_suffix = "positions"
    matrix_suffix = "matrice"
    unknown_suffix = "inconnus"

    # chargement des entrées
    the_thesaurus = CogMaps.load_thesaurus_map(thesaurus_filename)
    the_weights = CogMaps.load_weights(weights_filename)
    the_cog_maps = CogMaps(cog_maps_filename)
    all_maps, all_reports = the_cog_maps.apply_many(the_thesaurus, with_unknown=with_unknown)

    # on produit tout les résultats
    for a_lvl, a_map in all_maps.items():
        a_map.dump(get_name(a_lvl))
        a_map.dump_occurrences_many(get_name(f"{a_lvl}_{occurrences_suffix}"), the_weights)
        a_map.dump_occurrences_in_position(get_name(f"{a_lvl}_{positions_suffix}"))
        a_map.weights = the_weights[weights_name]
        a_map.dump_matrix(get_name(f"{a_lvl}_{matrix_suffix}_{weights_name}"))

    for a_lvl, a_report in all_reports.items():
        a_report.dump(get_name(f"{a_lvl}_{unknown_suffix}"))

    return all_maps


WITH_UNKNOWNS = False
DEBUG = True
if __name__ == "__main__" and not DEBUG:
    generate_results(
        OUTPUT_DIR, CM_LA_MINE_FILENAME, THESAURUS_FILENAME, WEIGHTS_MAP_FILENAME, with_unknown=WITH_UNKNOWNS
    )
    generate_results(
        OUTPUT_DIR, CM_FUTUR_FILENAME, THESAURUS_FILENAME, WEIGHTS_MAP_FILENAME, with_unknown=WITH_UNKNOWNS
    )


if __name__ == "__main__" and DEBUG:
    test_thesaurus = CogMaps.load_thesaurus_map(THESAURUS_FILENAME)
    test_maps = CogMaps(CM_SMALL_FILENAME)
    test_weights = CogMaps.load_weights(WEIGHTS_MAP_FILENAME)

    # test_maps.thesaurus = test_thesaurus[CONCEPT_LVL]
    # # test_weights = CogMaps.load_weights(WEIGHTS_MAP_FILENAME)
    # test_mother, test_report = test_maps.apply(with_unknown=False)
    # pprint(test_report.cog_maps)

    # pprint(test_maps.matrix)
    test_maps.weights = test_weights[DEFAULT_WEIGHTS_NAME]
    test_maps.dump_matrix("output/test_matrice.csv")
