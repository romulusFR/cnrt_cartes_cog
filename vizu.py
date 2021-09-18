"""Vizualisation graphique"""
# %%

import locale
from unicodedata import normalize
from functools import cmp_to_key
from collections import defaultdict
from pprint import pprint

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn as sk
from sklearn.cluster import SpectralClustering

# using your default locale (user settings)
locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")

from cog_maps import CogMaps, CM_LA_MINE_FILENAME, THESAURUS_FILENAME, WEIGHTS_MAP_FILENAME


def normalize_row(m):
    return np.diag(1 / m.diagonal()) @ m


def normalize_col(m):
    return m @ np.diag(1 / m.diagonal())


def normalize_sym(m):
    dsqrt = np.diag(np.power(m.diagonal(), -0.5))
    return dsqrt @ m @ dsqrt


def normalize_sum(m):
    d_m = np.diag(m.diagonal())
    return 2 / (d_m @ (1 / m) + (1 / m) @ d_m)


# %% les cog_maps
weights = CogMaps.load_weights(WEIGHTS_MAP_FILENAME)
thesaurus = CogMaps.load_thesaurus_map(THESAURUS_FILENAME)
base_cog_maps = CogMaps(CM_LA_MINE_FILENAME)
cog_maps, _ = base_cog_maps.apply_many(thesaurus)

# %%
# les dataframes
the_cog_maps = cog_maps["mother"]
the_cog_maps.weights = weights["pos_6"]
matrix = the_cog_maps.matrix
df = pd.DataFrame(matrix).fillna(0.0)
sorted_words = sorted(the_cog_maps.words, key=lambda x: normalize("NFD", x))
df = df.reindex(columns=sorted_words, copy=False).reindex(index=sorted_words, copy=False)

# df.sort_index(axis=0, inplace=True, key =lambda s: s.str.normalize("NFD"))
# df = df[sorted_cols]
# cmp_to_key(locale.strcoll)
# .melt(ignore_index = False,  var_name="col", value_name="nb")

dfn = pd.DataFrame(normalize_sym(df.to_numpy()))
dfn.set_index(df.index, inplace=True)
dfn.columns = sorted_words

# %%
# heatmap de base
# fig, ax = plt.subplots(figsize=(16, 16))
# # https://stackoverflow.com/questions/50754471/seaborn-heatmap-not-displaying-all-xticks-and-yticks
# # mask = np.triu(np.ones_like(dfn)),
# sns.heatmap(dfn, xticklabels=True, yticklabels=True)

# %%
NB_CLUSTERS = 30

sc = SpectralClustering(NB_CLUSTERS, affinity="precomputed")
clusters = sc.fit_predict(dfn)
positions = np.argsort(clusters)
# print(clusters)
# print(positions)

# normalisé et réordonné
dfn_c = dfn.reindex(index=[sorted_words[i] for i in positions], columns=[sorted_words[i] for i in positions])

inverse = defaultdict(list)
for i, c in enumerate(clusters):
    inverse[c].append(sorted_words[i])

# les clusters
pprint(inverse)

# la heatmap près classement
fig, ax = plt.subplots(figsize=(12, 14))
sns.heatmap(dfn_c, xticklabels=True, yticklabels=True)

# dfn.sort_index(axis=0, inplace=True, positions)
# df = df[sorted_cols]

# %%

# sans normalization


# fig, ax = plt.subplots(figsize=(16, 16))
# # https://stackoverflow.com/questions/50754471/seaborn-heatmap-not-displaying-all-xticks-and-yticks
# # mask = np.triu(np.ones_like(dfn)),
# sns.heatmap(df, xticklabels=True, yticklabels=True)


# clusters = sc.fit_predict(df)
# positions = np.argsort(clusters)
# print(clusters)
# print(positions)

# df_c = df.reindex(index=[sorted_words[i] for i in positions], columns=[sorted_words[i] for i in positions])

# inverse = defaultdict(list)
# for i, c in enumerate(clusters):
#     inverse[c].append(sorted_words[i])

# pprint(inverse)

# fig, ax = plt.subplots(figsize=(16, 16))
# sns.heatmap(df_c, xticklabels=True, yticklabels=True)
