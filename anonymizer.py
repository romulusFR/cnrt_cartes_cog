"""Permet de transformer un csv de fichier de données personnelles sur les cartes en une version "anonymisée"."""

# %%
from math import floor, isnan, nan
from functools import partial
from pathlib import Path
from collections import defaultdict
from typing import Any

import pandas as pd


PERSONAL_DATA_FILE = Path("anonymization/personal_data.csv")

#%%


def int_to_interval(n, width):
    """Transforme un entier en son intervalle à width près"""
    if isnan(n):
        return n
    quotient = floor(n / width)
    return pd.Interval(width * quotient, width * (quotient + 1), closed="left")


def get_data(file, drop=False) -> pd.DataFrame:
    """Lit, caste et transforme les données sensibles"""
    # lecture
    df = pd.read_csv(file, sep=";")
    # l'index est le numéro d'enquête
    df.set_index("numero_enquete", drop=True, inplace=True)
    # cast de la date
    df["date"] = pd.to_datetime(df["date"])

    # cast des attributs booléens
    bool_attrs = {"travail_mine", "famille_mine", "habitant_nc", "habite_ailleurs_nc"}
    bool_mapper = lambda word: word.lower() == "oui"
    for attr in bool_attrs:
        df[attr] = df[attr].apply(bool_mapper)

    # cast de la commune_minière "tri valuée"
    tri_mapper: dict[str, Any] = defaultdict(lambda: nan)
    tri_mapper |= {"Minière": 1, "Non minière": -1, "Mixte": 0}

    df["commune_miniere"] = df["commune_miniere"].apply(lambda x: tri_mapper[x])

    # intervalles d'anonymisation pour les durées
    interval_mapper = {"age": 10, "duree_residence": 10, "duree_presence_nc": 10, "duree_travail_mine": 5}
    for attr, width in interval_mapper.items():
        df[f"{attr}_interval"] = df[attr].apply(partial(int_to_interval, width=width))

    if drop:
        for serie in interval_mapper:
            df.drop(serie, inplace=True, axis=1)

    return df


if __name__ == "__main__":
    data = get_data(PERSONAL_DATA_FILE, drop=True)
    data.to_csv(PERSONAL_DATA_FILE.with_stem(PERSONAL_DATA_FILE.stem + "_anonymized"))


# %%
