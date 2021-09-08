# pylint: disable =  unused-import, missing-class-docstring, missing-function-docstring, too-few-public-methods, no-self-use
"""Tests"""

from pathlib import Path


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
    def test_load(self):
        cog_map = CogMaps()
        cog_map.load(TEST_FILENAME)
        assert len(cog_map) == 9
        assert cog_map.cog_maps[1] == ["pollution", "inondation", "boom", "travail", "retombée"]

    def test_dump(self, tmp_path):
        cog_map = CogMaps(TEST_FILENAME)
        assert len(cog_map) == 9
        filename = tmp_path / "dump.csv"
        cog_map.dump(filename)
        assert filename.read_text() == DUMP_CONTENT

    def test_pivot(self):
        cog_map = CogMaps(TEST_FILENAME)
        cog_map.pivot()
        assert len(cog_map.cog_index)  == 42
        words = {word for words in cog_map.cog_maps.values() for word in words}
        assert cog_map.cog_index.keys() == words
