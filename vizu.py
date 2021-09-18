"""Vizualisation graphique"""
# %%

import locale
from unicodedata import normalize
from functools import cmp_to_key
from collections import defaultdict
from pprint import pprint
from itertools import accumulate

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn as sk


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



weights = CogMaps.load_weights(WEIGHTS_MAP_FILENAME)
thesaurus = CogMaps.load_thesaurus_map(THESAURUS_FILENAME)
base_cog_maps = CogMaps(CM_LA_MINE_FILENAME)
cog_maps, _ = base_cog_maps.apply_many(thesaurus)

# %%
# les dataframes
the_cog_maps = cog_maps["mother"]
the_cog_maps.weights = weights["pos_3_arith"]
matrix = the_cog_maps.matrix

# reset de la diagonale
# for word in the_cog_maps.words:
#     matrix[word][word] = 0.0

df = pd.DataFrame(matrix).fillna(0.0)
sorted_words = sorted(the_cog_maps.words, key=lambda x: normalize("NFD", x))
df = df.reindex(columns=sorted_words, copy=False).reindex(index=sorted_words, copy=False)

df.describe()

# df.sort_index(axis=0, inplace=True, key =lambda s: s.str.normalize("NFD"))
# df = df[sorted_cols]
# cmp_to_key(locale.strcoll)
# .melt(ignore_index = False,  var_name="col", value_name="nb")

# %%
# sans normalization


fig, ax = plt.subplots(figsize=(16, 16))
# https://stackoverflow.com/questions/50754471/seaborn-heatmap-not-displaying-all-xticks-and-yticks
# mask = np.triu(np.ones_like(dfn)),
sns.heatmap(df, xticklabels=True, yticklabels=True)

# %%

NB_CLUSTERS = 9
THRESHOLD = 2.0
from sklearn.cluster import AffinityPropagation
from sklearn.cluster import SpectralClustering
from sklearn.cluster import KMeans

clustering = SpectralClustering(NB_CLUSTERS, affinity="precomputed")
# clustering = KMeans(NB_CLUSTERS)
# clustering = AffinityPropagation(random_state=None, affinity="euclidean")

# %%

clusters = clustering.fit_predict(df[df >= THRESHOLD].fillna(0.0))
positions = np.argsort(clusters)
clustered_words = [sorted_words[i] for i in positions]
df_c = df.reindex(index=clustered_words, columns=clustered_words)

clusters_idx = defaultdict(list)
for i, c in enumerate(clusters):
    clusters_idx[c].append(sorted_words[i])

# pprint(clusters_idx)


sns.despine()
fig, ax = plt.subplots(figsize=(16, 16))
heatmap = sns.heatmap(df_c, xticklabels=True, yticklabels=True)
widths = list(accumulate(map(len,clusters_idx.values())))
ax.hlines(widths[:-1:], *ax.get_xlim(), colors="white")
ax.vlines(widths[:-1:], *ax.get_ylim(), colors="white")


# %% version normalisée

nn = normalize_sym(df.to_numpy())
np.fill_diagonal(nn, 0.0)
dfn = pd.DataFrame(nn)
dfn.set_index(df.index, inplace=True)
dfn.columns = sorted_words

fig, ax = plt.subplots(figsize=(16, 16))
# https://stackoverflow.com/questions/50754471/seaborn-heatmap-not-displaying-all-xticks-and-yticks
# mask = np.triu(np.ones_like(dfn)),
sns.heatmap(dfn, xticklabels=True, yticklabels=True)

# %%


clusters = clustering.fit_predict(dfn[dfn >= 0.01].fillna(0.0))
positions = np.argsort(clusters)
clustered_words = [sorted_words[i] for i in positions]
dfn_c = dfn.reindex(index=clustered_words, columns=clustered_words)

clusters_idx = defaultdict(list)
for i, c in enumerate(clusters):
    clusters_idx[c].append(sorted_words[i])

sns.despine()
fig, ax = plt.subplots(figsize=(16, 16))
heatmap = sns.heatmap(dfn_c, xticklabels=True, yticklabels=True)
# BUG : ordre des lignes KO
widths = list(accumulate(map(len,clusters_idx.values())))
ax.hlines(widths[:-1:], *ax.get_xlim(), colors="white")
ax.vlines(widths[:-1:], *ax.get_ylim(), colors="white")

