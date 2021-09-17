"""Juste la définition des poids"""

from math import exp

MAX_LEN = 15
OLD_WEIGHTS = {
    # toutes les positions ont un poids de 1.0
    "any_1": {i: 1.0 for i in range(1, MAX_LEN + 1)},
    # la première position à un poids de 1.0, les autres 0.0
    "first_1": {i: 1.0 for i in range(1, 2)},
    # idem first_1 mais avec les 2 premières positions
    "first_2": {i: 1.0 for i in range(1, 3)},
    # idem first_1 mais avec les 3 premières positions
    "first_3": {i: 1.0 for i in range(1, 4)},
    # idem first_1 mais avec les 4 premières positions
    "first_4": {i: 1.0 for i in range(1, 5)},
    # idem first_1 mais avec les 5 premières positions
    "first_5": {i: 1.0 for i in range(1, 6)},
    # le poids est de 1/n : 1.0, 0.5, 0.333, 0.25 ...
    "1_on_n": {i: 1 / i for i in range(1, MAX_LEN + 1)},
    # le poids est de 1/n*n : 1.0, 0.25, 0.111, 0.0625 ...
    "1_on_n_square": {i: 1 / (i ** 2) for i in range(1, MAX_LEN + 1)},
    # le poids est en exponentielle(1-i) : 1.0, 0.37, 0.14, 0.05 ...
    "exp_minus_n_plus_1": {i: exp(-i + 1) for i in range(1, MAX_LEN + 1)},
    # décroissance linéaire : 1.0, 0.9, 0.8, 0.7 ...
    "1_minus_0_1_times_n": {i: max(0.0, 1 - 0.1 * (i - 1)) for i in range(1, MAX_LEN + 1)},
    # décroissance linéaire : 1.0, 0.8, 0.6, 0.4 ...
    "1_minus_0_2_times_n": {i: max(0.0, 1 - 0.2 * (i - 1)) for i in range(1, MAX_LEN + 1)},
}

WEIGHTS = {
    # arithmétique sur base de longueur MAX_LEN = 15
    # 16/16, 15/16, 14/16 ..., 1/16
    "arithmetique": {i: (MAX_LEN + 1 - i) / MAX_LEN for i in range(1, MAX_LEN + 1)},
    # inverse de la position
    "inverse": {i: 1 / i for i in range(1, MAX_LEN + 1)},
    # première position uniquement
    "pos_1": {i: 1.0 for i in range(1, 1 + 1)},
    # trois premières positions uniquement, toutes à 1.0
    "pos_3": {i: 1.0 for i in range(1, 3 + 1)},
    # six première position uniquement, toutes à 1.0
    "pos_6": {i: 1.0 for i in range(1, 6 + 1)},
    # trois premières positions uniquement,
    # avec poids arithmétiquement décroissant 3/3, 2/3, 1/3, 0 ...
    "pos_3_arith": {i: (3 - i + 1) / 3 for i in range(1, 3 + 1)},
    # six premières positions uniquement,
    # avec poids arithmétiquement décroissant 6/6, 5/6, 4/6 ...
    "pos_6_arith": {i: (6 - i + 1) / 6 for i in range(1, 6 + 1)},
}
