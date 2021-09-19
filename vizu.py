"""Vizualisation graphique"""
# %%

import locale
from typing import Callable
from unicodedata import normalize
from functools import cmp_to_key
from collections import defaultdict
from pprint import pprint
from itertools import accumulate, chain

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# import sklearn as sk
import networkx as nx
import sklearn.cluster as sk


from cog_maps import CogMaps, CM_LA_MINE_FILENAME, THESAURUS_FILENAME, WEIGHTS_MAP_FILENAME


np.set_printoptions(precision=2)
pd.set_option("display.precision", 2)
# using your default locale (user settings)
locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")

# global constants
weights = CogMaps.load_weights(WEIGHTS_MAP_FILENAME)
thesaurus = CogMaps.load_thesaurus_map(THESAURUS_FILENAME)
base_cog_maps = CogMaps(CM_LA_MINE_FILENAME)
cog_maps, _ = base_cog_maps.apply_many(thesaurus)

# level_name: str = "mother",
# weights_name: str = "pos_3_arith",

# the_cog_maps = cog_maps[level_name]
# the_cog_maps.weights = weights[weights_name]


def cog_maps_to_df(cog_maps):
    df = pd.DataFrame(cog_maps.matrix).fillna(0.0)
    # on trie en gérant les accents
    alpha_words = sorted(cog_maps.words, key=lambda x: normalize("NFD", x))
    # on réorganise lignes et colonnes
    df = df.reindex(columns=alpha_words, copy=False).reindex(index=alpha_words, copy=False)

    return df
    # df.describe()


def heatmap(df: pd.DataFrame, limits=None):
    sns.despine()
    fig, ax = plt.subplots(figsize=(16, 16))

    # https://stackoverflow.com/questions/50754471/seaborn-heatmap-not-displaying-all-xticks-and-yticks
    # mask = np.triu(np.ones_like(dfn)),
    sns.heatmap(df, xticklabels=True, yticklabels=True, cmap="RdYlGn_r")
    if limits:
        ax.hlines(limits[:-1:], *ax.get_xlim(), colors="white")
        ax.vlines(limits[:-1:], *ax.get_ylim(), colors="white")
    plt.show()


#     normalizer: Callable = lambda m: m,


def clusterize(df: pd.DataFrame, n_clusters=5):
    # https://scikit-learn.org/stable/modules/classes.html#module-sklearn.cluster

    # choix d'un algo de clustering
    # clustering = sk.SpectralClustering(n_clusters, affinity="precomputed")
    clustering = sk.AffinityPropagation(random_state=None, damping = 0.5, affinity="precomputed")
    # clustering = sk.AgglomerativeClustering(n_clusters=n_clusters)
    # clustering = sk.DBSCAN(metric="precomputed")
    # clustering = sk.KMeans(n_clusters)

    clusters = clustering.fit_predict(df)
    # à chaque index de clustering, la liste des mots
    clusters_idx = defaultdict(list)
    for i, cluster in enumerate(clusters):
        clusters_idx[cluster].append(df.index[i])
    return clusters_idx
    # positions = np.argsort(clusters)
    # clustered_words = [sorted_words[i] for i in positions]
    # df_c = df.reindex(index=clustered_words, columns=clustered_words)


def test():
    test_cog_maps = CogMaps("input/cartes_cog_small_cooc.csv")
    # test_cog_maps.weights = weights["pos_1"]
    test_df = cog_maps_to_df(test_cog_maps)
    given_df = test_df  # np.exp(1-the_df)
    print(given_df)
    G = nx.Graph(given_df)
    nx.draw_spring(G, with_labels=True)
    # the_df = cog_maps_to_df()
    # heatmap(the_df)
    idx = clusterize(given_df, n_clusters=3)
    pprint(idx)


if __name__ == "__main__":
    # mise en place
    level_name = "gd_mother"
    weights_name = "pos_1"
    the_cog_maps = cog_maps[level_name]
    the_cog_maps.weights = weights[weights_name]
    the_df = cog_maps_to_df(the_cog_maps)

    # choix de la variante qu'on va clusteriser
    #  - distance/affinité
    #  - seuillage
    #  - normalisation

    # heatmap(the_df_to_cluster)
    # https://stackoverflow.com/questions/18594469/normalizing-a-pandas-dataframe-by-row
    


    # the_df_to_cluster =  np.exp(1 - the_df)
    # the_df_to_cluster = the_df
    the_df_to_cluster = the_df.copy()
    
    the_df_to_cluster = the_df_to_cluster.div(the_df_to_cluster.max(axis=1), axis=0)  # np.exp(1 - the_df)
    # np.fill_diagonal(the_df_to_cluster.values, 0)


    # le résultat du clustering
    the_clusters_idx = clusterize(the_df_to_cluster)
    # on va réidenxer selont l'ordre donné par les clusters
    sorted_index = [word for _, words in sorted(the_clusters_idx.items()) for word in words]
    the_df_clustered = the_df_to_cluster.reindex(index=sorted_index, columns=sorted_index)

    # on va mettre une petite ligne entre les clusters
    limits = list(accumulate([len(cat) for _, cat in sorted(the_clusters_idx.items())]))
    heatmap(the_df_clustered, limits)

    # le contenu des cluster, id les groupes dans les lignes blanches
    for idx, clust in sorted(the_clusters_idx.items()):
        print(idx, clust)
