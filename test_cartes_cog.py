# pylint: disable =  unused-import, missing-class-docstring, missing-function-docstring, too-few-public-methods, no-self-use
"""Tests de la lib CogMaps"""

# %%

from collections import defaultdict, Counter
from pathlib import Path
import pytest
from cog_maps import CogMaps, CSV_PARAMS, ENCODING, DEFAULT_WEIGHTS_NAME

COGMAPS_FILENAME = Path("input/cartes_cog_small.csv")
WEIGHTS_FILENAME = Path("input/coefficients.csv")
DUMP_CONTENT = """1;pollution;inondation;boom;travail;retombée
2;richesse;malédiction;travail;destruction;histoire;frein;blocage;coutumier
4;travail;pollution;plainte
5;argent;pollution;nickel;production;nature;réparation;mer;inégalité
6;extraction;montagne;pollution;mineur;train;diversité;évolution
7;pollution;nickel;argent;mer;camion
8;centre minier;village;économie;production;travail;environnement;revenu
9;camion;contracteur;caillou;terre rouge;géologie;laboratoire;perle;argent;travail;aide
10;emploi;environnement;pollution;aide;reboisement;porte d’entrée;inondation
"""


class TestCognitiveMap:
    def test_clean_words(self):
        assert callable(CogMaps.clean_word)
        assert CogMaps.clean_word("  MoT ") == "mot"

    def test_cog_init_empty(self):
        test_maps = CogMaps()
        assert len(test_maps) == 0
        assert len(test_maps.cog_maps) == 0
        assert len(test_maps.index) == 0

    def test_cog_init_filename(self):
        test_maps = CogMaps(COGMAPS_FILENAME)
        assert len(test_maps) == 9
        assert len(test_maps.cog_maps) == 9
        assert test_maps.cog_maps[1] == ["pollution", "inondation", "boom", "travail", "retombée"]

    def test_dump(self, tmp_path):
        test_maps = CogMaps(COGMAPS_FILENAME)
        filename = tmp_path / "dump.csv"
        test_maps.dump(filename)
        assert filename.read_text(encoding=ENCODING) == DUMP_CONTENT

    def test_cog_maps_assignment(self):
        test_maps = CogMaps()
        with pytest.raises(TypeError, match=r".*assignment.*"):
            test_maps.cog_maps = []

    def test_index(self):
        test_maps = CogMaps(COGMAPS_FILENAME)
        assert len(test_maps.index) == 42
        words = {word for words in test_maps.cog_maps.values() for word in words}
        # on a bien indexé tous les mots
        assert test_maps.index.keys() == words
        # on a bien autant de positions qu'il y avait de mots énoncés
        assert sum(len(pos) for pos in test_maps.index.values()) == sum(
            len(words) for words in test_maps.cog_maps.values()
        )

    def test_cog_index_assignment(self):
        test_maps = CogMaps()
        with pytest.raises(TypeError, match=r".*assignment.*"):
            test_maps.index = {}

    # def test_load_weights(self):
    #     weights = CogMaps.load_weights(WEIGHTS_FILENAME)
    #     ref_weights = defaultdict(float) | {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2}
    #     for pos in weights:
    #         assert weights[pos] == ref_weights[pos]

    # def test_weights(self):
    #     test_maps = CogMaps(COGMAPS_FILENAME)
    #     test_maps.weights = CogMaps.load_weights(WEIGHTS_FILENAME)
    #     ref_weights = defaultdict(float) | {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2}
    #     for pos in test_maps.weights:
    #         assert test_maps.weights[pos] == ref_weights[pos]

    def test_occurrences_default_weights(self):
        test_maps = CogMaps(COGMAPS_FILENAME)
        occurrences = test_maps.occurrences
        assert len(occurrences) == 42
        bag = [word for words in test_maps.cog_maps.values() for word in words]
        assert occurrences == Counter(bag)

    def test_occurrences_custom_weights(self):
        test_maps = CogMaps(COGMAPS_FILENAME)
        test_maps.weights = CogMaps.load_weights(WEIGHTS_FILENAME)[DEFAULT_WEIGHTS_NAME]
        occurrences = test_maps.occurrences
        assert len(occurrences) == 42
        assert occurrences["travail"] == 0.82 + 0.88 + 1.00 + 0.76 + 0.53

    def test_occurrences_dump_occurrences(self, tmp_path):
        test_maps = CogMaps(COGMAPS_FILENAME)
        file_no_weights = tmp_path / "dump_no_weights.csv"
        test_maps.dump_occurrences(file_no_weights)
        test_maps.weights = CogMaps.load_weights(WEIGHTS_FILENAME)[DEFAULT_WEIGHTS_NAME]
        file_weights = tmp_path / "dump_weights.csv"
        test_maps.dump_occurrences(file_weights)

        content_no_weights = {}
        for line in file_no_weights.read_text(encoding=ENCODING).split("\n")[1:]:
            cols = line.split(CSV_PARAMS["delimiter"])
            if len(cols) == 3:
                content_no_weights[cols[0]] = cols[1:]
                assert float(cols[1]) == float(cols[2])
        assert list(content_no_weights.keys()) == sorted(list(test_maps.words))

        content_weights = {}
        for line in file_weights.read_text(encoding=ENCODING).split("\n")[1:]:
            cols = line.split(CSV_PARAMS["delimiter"])
            if len(cols) == 3:
                content_weights[cols[0]] = cols[1:]
                assert float(cols[1]) >= float(cols[2])
        assert list(content_weights.keys()) == sorted(list(test_maps.words))

    def test_occurrences_dump_occurrences_in_position(self, tmp_path):
        test_maps = CogMaps(COGMAPS_FILENAME)
        filename = tmp_path / "dump_position.csv"
        test_maps.dump_occurrences_in_position(filename)
