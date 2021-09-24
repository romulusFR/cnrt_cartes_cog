"""Export des cartes cog dans un format json pour vega-lite"""
# pylint: disable=unused-import
# %%

from itertools import islice, accumulate
from collections import defaultdict
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import Tuple, Optional
import json


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, PowerNorm, Normalize
import seaborn as sns
import networkx as nx

from cog_maps import CogMaps, CM_LA_MINE_FILENAME, THESAURUS_FILENAME, WEIGHTS_MAP_FILENAME, DEFAULT_WEIGHTS, LEVELS


thesaurus = CogMaps.load_thesaurus_map(THESAURUS_FILENAME)
weights = CogMaps.load_weights(WEIGHTS_MAP_FILENAME)
mine_map = CogMaps(CM_LA_MINE_FILENAME)


all_maps, report = mine_map.apply_many(thesaurus, with_unknown=False)
for name, a_map in all_maps.items():
    a_map.weights = DEFAULT_WEIGHTS

# %%


def mk_unique_id():
    counter = 0

    def inner():
        nonlocal counter
        counter += 1
        return counter

    return inner


unique_id = mk_unique_id()


ROOT_LVL = "racine"


@dataclass
class WordInfo:
    """Classe pour l'index de tous les mots"""

    id: int
    word: Tuple[str, str]
    pid: Optional[int]
    parent: Optional[Tuple[str, str]]
    weight: float = 0.0
    depth: int = 0


# la racine
global_word_map = {(ROOT_LVL, ROOT_LVL): WordInfo(id=0, word=(ROOT_LVL, ROOT_LVL), pid=None, parent=None)}
lvl_last = LEVELS[-1]


depth = 0

# on commence par le niveau le plus haut : les grand-mères
for word in thesaurus[lvl_last].values():
    weight = all_maps[lvl_last].occurrences[word]
    global_word_map[(lvl_last, word)] = WordInfo(
        id=unique_id(), word=(lvl_last, word), pid=0, parent=(ROOT_LVL, ROOT_LVL), weight=weight, depth=depth
    )

# du plus général au plus précis :
# mother gd_mother
# concept mother
# base concept

for lvl_w, lvl_p in zip(LEVELS[::-1][1::], LEVELS[::-1]):
    print(lvl_w, lvl_p)
    depth += 1
    for word, parent in thesaurus[lvl_p].items():
        # print("    ", word, parent)
        # print("    ", global_word_map[(lvl_p, parent)].pid)
        weight = all_maps[lvl_w].occurrences.get(word)
        global_word_map[(lvl_w, word)] = WordInfo(
            id=unique_id(),
            word=(lvl_w, word),
            pid=global_word_map[(lvl_p, parent)].id,
            parent=(lvl_p, parent),
            weight=weight,
            depth=depth,
        )


print(global_word_map[("base", "travail")])
print(global_word_map[("concept", "emploi")])
print(global_word_map[("mother", "emploi")])
print(global_word_map[("gd_mother", "travail")])


# le format ciblé
# { "id": 1, "relief": 0.228, "name": "Complaints" },
# { "id": 2, "relief": 0.37859110586383315, "name": "Credit card", "parent": 1, "size": 2541 }


a_wi = global_word_map[("base", "travail")]
# {detail.word[0]}-
objects = [
    {"id": detail.id, "name": f"{detail.word[1]}", "weight": detail.weight, "parent": detail.pid, "depth": detail.depth}
    for detail in global_word_map.values()
    if detail.weight is not None
]
with open("viz/data/thesaurus.json", mode="w", encoding="utf-8") as fp:
    json.dump(objects, fp)




max_weight = max(detail.weight for detail in global_word_map.values() if detail.weight is not None)
print(max_weight)
