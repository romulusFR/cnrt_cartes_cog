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
import math


from cog_maps import (
    CogMaps,
    CM_LA_MINE_FILENAME,
    THESAURUS_FILENAME,
    WEIGHTS_MAP_FILENAME,
    DEFAULT_WEIGHTS,
    LEVELS,
    BASE_LVL,
    CONCEPT_LVL,
    MOTHER_LVL,
    GD_MOTHER_LVL,
)

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

    id: int  # pylint: disable=invalid-name
    word: Tuple[str, str]
    pid: Optional[int]
    parent: Optional[Tuple[str, str]]
    weight: float = 0.0
    depth: int = 0


# la racine
ROOT_NAME = "racine"
LVL_LAST = LEVELS[-1]
global_word_map = {(ROOT_NAME, ROOT_NAME): WordInfo(id=0, word=(ROOT_NAME, ROOT_NAME), pid=None, parent=None, depth=0)}

ROOT_WEIGHT = 0
DEPTH = 1
# on commence par le niveau le plus haut : les grand-mères
print(f"ajout {LEVELS[-1]}")
for word in set(thesaurus[LVL_LAST].values()):
    weight = all_maps[LVL_LAST].occurrences[word]
    ROOT_WEIGHT += weight
    global_word_map[(LVL_LAST, word)] = WordInfo(
        id=unique_id(), word=(LVL_LAST, word), pid=0, parent=(ROOT_NAME, ROOT_NAME), weight=weight, depth=DEPTH
    )

global_word_map[(ROOT_NAME, ROOT_NAME)].weight = ROOT_WEIGHT

# du plus général au plus précis :
# mother gd_mother
# concept mother
# base concept

for lvl_w, lvl_p in zip(LEVELS[::-1][1::], LEVELS[::-1]):
    print(f"ajout {lvl_w} -> {lvl_p}")
    DEPTH += 1
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
            depth=DEPTH,
        )


print(global_word_map[(BASE_LVL, "travail")])
print(global_word_map[(CONCEPT_LVL, "emploi")])
print(global_word_map[(MOTHER_LVL, "emploi")])
print(global_word_map[(GD_MOTHER_LVL, "travail")])


# le format ciblé
# { "id": 1, "relief": 0.228, "name": "Complaints" },
# { "id": 2, "relief": 0.37859110586383315, "name": "Credit card", "parent": 1, "size": 2541 }


a_wi = global_word_map[(BASE_LVL, "travail")]
# {detail.word[0]}-
objects = [
    {
        "id": detail.id,
        "name": f"{detail.word[1]}",
        "lweight": round(detail.weight, 2) if detail.depth == 4 else None,
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
    """Vérifie si la somme des foils vaut bien celle du père (aux arrondis float près)"""
    ref = global_word_map[("gd_mother", lvl_1_word)]

    sons = [
        global_word_map[("mother", word)] for word, parent in thesaurus[GD_MOTHER_LVL].items() if parent == lvl_1_word
    ]

    print("ref.weight =", ref.weight)
    print("sons.weight =", sum(map(lambda x: x.weight, sons)))
    print("sons =", list(map(lambda x: x.word[1], sons)))


verif_sum("nickel")
verif_sum("travail")

# verdict : OK

# %%
PRINT_THESAURUS = False
if PRINT_THESAURUS:
    with open("viz/data/thesaurus.json", mode="w", encoding="utf-8") as fp:
        json.dump(objects, fp, indent=4, ensure_ascii=False)


max_weight = max(detail.weight for detail in global_word_map.values() if detail.weight is not None)
print(f"max_weight={max_weight}")


# %%

# export de la matrice

# le format ciblé
# { "src": "pollution", "dst": "patate", "weight": 2.32113 }


concept_map = all_maps[CONCEPT_LVL]


# for src, out in concept_map.matrix.items():
#     for dst, weight in out.items():
#         # print(src, dst, weight)
#         pass

# matrix_obj = [
#     {"lvl":lvl, "src": src, "dst": dst, "weight": round(all_maps[lvl].matrix[src][dst],2)}
#     for lvl in LEVELS[::]
#     for src in all_maps[lvl].words
#     for dst in all_maps[lvl].words
#     if src != dst
#     # if weight > 0.0
# ]

matrix_obj = [
    {"lvl":lvl, "src": src, "dst": dst, "weight": round(weight,2), "normal_weight": round(weight/sum(out.values()),2)}
    for lvl in LEVELS[::]
    for src, out in all_maps[lvl].matrix.items()
    for dst, weight in out.items()
    if src != dst
    # if weight > 0.0
]

PRINT_MATRIX = True
if PRINT_MATRIX:
    with open("viz/data/matrix_inverse.json", mode="w", encoding="utf-8") as fp:
        json.dump(matrix_obj, fp, indent=4, ensure_ascii=False)
