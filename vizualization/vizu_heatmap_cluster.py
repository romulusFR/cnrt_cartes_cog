"""Vizualisation graphique

Ici, une heatmap de seaborn avec reindexation des mots par clustering sur les co-occurences normalisées
"""
# pylint: disable=unused-import

# %%

import locale
from typing import Callable
import unicodedata
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
    """Charge une caret cognitive en DataFrame pandas"""
    df = pd.DataFrame(cog_maps.matrix).fillna(0.0)
    # on trie en gérant les accents
    alpha_words = sorted(cog_maps.words, key=lambda x: unicodedata.normalize("NFD", x))
    # on réorganise lignes et colonnes
    df = df.reindex(columns=alpha_words, copy=False).reindex(index=alpha_words, copy=False)

    return df
    # df.describe()


def heatmap(df: pd.DataFrame, limits=None):
    """Affiche une Heatmap seaborn à partir d'un DataFrame"""
    sns.despine()
    _, ax = plt.subplots(figsize=(18, 16))

    # https://stackoverflow.com/questions/50754471/seaborn-heatmap-not-displaying-all-xticks-and-yticks
    sns.heatmap(df, xticklabels=True, yticklabels=True, cmap="RdYlGn_r")
    if limits:
        ax.hlines(limits[:-1:], *ax.get_xlim(), colors="white")
        ax.vlines(limits[:-1:], *ax.get_ylim(), colors="white")
    plt.show()


def normalize_sym(m):
    """normalisation symétrique : divise chaque valeur (i,j) par la valeur de sqrt(i,i) et sqrt(j,j), autrement dit (i,j) devient (i,j)/sqrt((i,i) * (j,j)).

    Utilisé pour obtenir le Symmetric Normalized Laplacian"""
    dsqrt = np.diag(np.power(m.diagonal(), -0.5))
    return dsqrt @ m @ dsqrt


def clusterize(df: pd.DataFrame, n_clusters=5, normalize=False, threshold=0.05):
    # https://scikit-learn.org/stable/modules/classes.html#module-sklearn.cluster

    # choix d'un algo de clustering
    # clustering = sk.SpectralClustering(n_clusters, affinity="precomputed")
    # clustering = sk.AffinityPropagation(random_state=None, damping = 0.5, affinity="precomputed")
    # clustering = sk.AgglomerativeClustering(n_clusters=n_clusters)
    # clustering = sk.DBSCAN(metric="precomputed")
    clustering = sk.KMeans(n_clusters)

    # choix de la variante qu'on va clusteriser
    #  - distance/affinité
    #  - seuillage
    #  - normalisation

    data = df.values.copy()

    if normalize:
        data = normalize_sym(data)
    data[data < threshold] = 0.0
    # data = np.exp(1-data)
    # np.fill_diagonal(tdata, 0)

    clusters = clustering.fit_predict(data)
    # à chaque index de clustering, la liste des mots
    clusters_idx = defaultdict(list)
    for i, cluster in enumerate(clusters):
        clusters_idx[cluster].append(df.index[i])
    return clusters_idx


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


def main():
    """Fonction principale :
    1. chargement
    2. clustering
    3. vizu heatmap avec séparation inter clusters
    """
    # mise en place
    level_name = "mother"
    weights_name = "pos_6_arith"
    the_cog_maps = cog_maps[level_name]
    the_cog_maps.weights = weights[weights_name]
    the_df = cog_maps_to_df(the_cog_maps)
    # the_df = cog_maps_to_df(CogMaps("input/cartes_cog_small_cooc.csv"))
    # heatmap(the_df_to_cluster)

    the_df_to_cluster = the_df.copy()

    # le résultat du clustering
    the_clusters_idx = clusterize(the_df_to_cluster, n_clusters=5, normalize=True)
    # on va réidenxer selont l'ordre donné par les clusters
    sorted_index = [word for _, words in sorted(the_clusters_idx.items()) for word in words]
    the_df_clustered = the_df_to_cluster.reindex(index=sorted_index, columns=sorted_index)

    # on va mettre une petite ligne entre les clusters
    limits = list(accumulate([len(cat) for _, cat in sorted(the_clusters_idx.items())]))
    heatmap(the_df_clustered, limits)

    # le contenu des cluster, id les groupes dans les lignes blanches
    for idx, clust in sorted(the_clusters_idx.items()):
        print(idx, clust)


if __name__ == "__main__":
    main()
