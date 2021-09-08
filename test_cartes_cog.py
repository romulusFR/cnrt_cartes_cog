# pylint: disable =  unused-import, missing-class-docstring, missing-function-docstring, too-few-public-methods, no-self-use
"""Tests"""

from pathlib import Path
import pytest
from cartes_cog import CogMaps

TEST_FILENAME = Path("input/cartes_cog_small.csv")
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
        test_maps = CogMaps(TEST_FILENAME)
        assert len(test_maps) == 9
        assert len(test_maps.cog_maps) == 9
        assert test_maps.cog_maps[1] == ["pollution", "inondation", "boom", "travail", "retombée"]

    def test_dump(self, tmp_path):
        test_maps = CogMaps(TEST_FILENAME)
        filename = tmp_path / "dump.csv"
        test_maps.dump(filename)
        assert filename.read_text() == DUMP_CONTENT

    def test_cog_maps_assignment(self):
        test_maps = CogMaps()
        with pytest.raises(TypeError, match=r".*assignment.*"):
            test_maps.cog_maps = {}

    def test_index(self):
        test_maps = CogMaps(TEST_FILENAME)
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

    # def test_hist(self):
    #     cog_map = CogMaps(TEST_FILENAME)
    #     cog_map.hist()
    #     assert len(cog_map.occurrences)  == 42
    #     bag = [word for words in cog_map.cog_maps.values() for word in words]
    #     assert sorted(cog_map.occurrences.elements()) == sorted(bag)
    