"""Export des cartes cog dans un format json pour vega-lite"""
# pylint: disable=unused-import
# %%

from itertools import islice, accumulate
from collections import defaultdict
from pathlib import Path
from dataclasses import asdict, dataclass
from typing import Tuple, Optional
import json
import logging


from cog_maps import CogMaps, CM_LA_MINE_FILENAME, THESAURUS_FILENAME, WEIGHTS_MAP_FILENAME, DEFAULT_WEIGHTS, LEVELS

logger = logging.getLogger(f"COGNITIVE_MAP.{__name__}")
if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.INFO)


thesaurus = CogMaps.load_thesaurus_map(THESAURUS_FILENAME)
weights = CogMaps.load_weights(WEIGHTS_MAP_FILENAME)
mine_map = CogMaps(CM_LA_MINE_FILENAME)


all_maps, report = mine_map.apply_many(thesaurus, with_unknown=False)
for name, a_map in all_maps.items():
    a_map.weights = weights["inverse"]

# %%


def mk_unique_id():
    """Generateur d'identifiant"""
    counter = 0

    def inner():
        nonlocal counter
        counter += 1
        return counter

    return inner


unique_id = mk_unique_id()


@dataclass
class WordInfo:
    """Classe pour l'index de tous les mots"""

    id: int
    word: Tuple[str, str]
    pid: Optional[int]
    parent: Optional[Tuple[str, str]]
    weight: float = 0.0
    depth: int = 0


ROOT_LVL = "racine"
# la racine
global_word_map = {(ROOT_LVL, ROOT_LVL): WordInfo(id=0, word=(ROOT_LVL, ROOT_LVL), pid=None, parent=None, depth=0)}
lvl_last = LEVELS[-1]


depth = 1
# on commence par le niveau le plus haut : les grand-mères
print(f"ajout {LEVELS[-1]}")
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
    print(f"ajout {lvl_w} -> {lvl_p}")
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
    {
        "id": detail.id,
        "name": f"{detail.word[1]}",
        "weight": round(detail.weight, 2),
        "parent": detail.pid,
        "depth": detail.depth,
    }
    for detail in global_word_map.values()
    if detail.weight is not None
]
# %%

# vérification de la somme du nickel de mere à gd mere


def verif_sum(lvl_1_word):

    ref = global_word_map[("gd_mother", lvl_1_word)]

    sons = [
        global_word_map[("mother", word)] for word, parent in thesaurus["gd_mother"].items() if parent == lvl_1_word
    ]

    print("ref.weight =", ref.weight)
    print("sons.weight =", sum(map(lambda x: x.weight, sons)))
    print("sons =", list(map(lambda x: x.word[1], sons)))

verif_sum("nickel")
verif_sum("travail")

# verdict : OK

# %%

with open("viz/data/thesaurus.json", mode="w", encoding="utf-8") as fp:
    json.dump(objects, fp, indent=4, ensure_ascii=False)


max_weight = max(detail.weight for detail in global_word_map.values() if detail.weight is not None)
print(f"max_weight={max_weight}")
