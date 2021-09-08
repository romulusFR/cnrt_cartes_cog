# Outil de calcul de cartes cognitives

La bibliothèque de base est dans le fichier [`cartes_cog.py`](cartes_cog.py).
Deux interfaces client existent avec les mêmes fonctionnalités :

- GUI (Graphic User Interface), [`gui.py`](gui.py) en TkInter
- CLI (Command Line Interface), [`cli.py`](cli.py)

## CHANGELOG

- 2021-09-09 :
  - ajout handler logger GUI
  - correction des filedialog de la GUI
- 2021-09-08 :
  - refactor complet POO
  - utilisation des poids pour le calcul de la matrice de similarité
- 2021-09-02 :
  - calcul de co-occurence à fenêtre
  - génération de graphes co-occurence avec fenêtre
  - ajout header occurences
  - ajout calcul des occurences pondérées par les positions
- 2021-09-01 :
  - support des deux cartes "la mine" et "la mine dans le futur"
  - valeurs par défaut des `filedialog` de la GUI
  - calcul du rapport des mots inconnus
  - normalisation des noms de fichiers
  - refator du calcul de co-occurences
  - genération des graphes de co-occurences
- 2021-07-26 :
  - première release

## Formats d'entrée

Le logiciel prends les entrée suivantes, toutes au format CSV (séparé par `;`) encodé en UTF-8, avec le point (`.`) comme séparateur décimal.

- une _base de données des mots énoncés_, dite _cartes cognitives_, à la structure suivante :
  - `identifiant; mot 1; mot 2; ...`. Les cartes peuvent avoir des longueurs différentes
  - **pas d'en-tête** dans la première ligne du fichier
- un _thésaurus_, dit aussi _ontologie_, qui aux mots énoncés fait correspondre un mot mère, dit aussi _concept_, à la structure suivante :
  - `mot mère; mot énoncé`.
  - **pas d'en-tête** dans la première ligne du fichier
- les _coefficients de pondération des occurences_, qui à chaque position donne un poids, typiquement décroissant avec le rang
  - `position;poids`
  - fichier **avec en-tête**

## Calcul

Pour une base de mots énoncés dont le nom de fichier est `$BD.csv`, le programme produit les fichiers résultats suivants :

- `$BD_occurences.csv` : pour chaque mot énoncé, le nombre de fois où il apparait dans la base
- `$BD_positions.csv` : pour chaque position, la liste des mots énoncés dans cette position et la liste de fois où ils y apparaissent. La deuxième colonne est celle des occurences pondérées par la position
- `$BD_meres.csv` : les cartes où les mots énoncés sont remplacés par leur mots mères associés, dites _cartes mères_. Un option permet de remplacer, ou pas, les mots énoncés qui n'ont pas de mot mère
- `$BD_inconnus.csv` : les mots des cartes qui n'apparaissent pas dans le thésaurus. Pour chaque mot inconnu, on donne les identifiants de carte où il apparaissent
- `$BD_occurences_meres.csv` : idem `$BD_occurences.csv` mais avec les cartes mères
- `$BD_positions_meres.csv` : idem `$BD_positions.csv` mais avec les cartes mères

## Entrées par défaut

Sans configuration, le calcul va être fait deux fois :

1. une fois sur les cartes _la mine_ avec comme entrées les cartes `input/cartes_cog_la_mine.csv` et le thésaurus `input/thesaurus_la_mine.csv`
2. une fois sur les cartes _la mine dans le futur_ avec comme entrées les cartes `input/cartes_cog_mine_futur.csv` et le thésaurus `input/thesaurus_mine_futur.csv`

Les exemples sont donnés dans le dossier [`input`](input/)

## Interface ligne de commande

La CLI a l'interface suivante. C'est la même chose que la GUI, qui exécute en fait essentiellement la fonction `generate_results` de la bibliothèque.

```raw
python cli.py -h
usage: cli.py [-h] [--ontology ONTOLOGY] [--cartes CARTES] [--directory DIRECTORY] [--unknown] [--verbose]

Outil de traitement des cartes cognitives

optional arguments:
  -h, --help            show this help message and exit
  --ontology ONTOLOGY, -o ONTOLOGY
                        fichier csv de description de l'ontologie, au format (concept, mot énoncé), par défaut 'input/thesaurus.csv'
  --cartes CARTES, -c CARTES
                        fichier csv des cartes cognitives, au format (id, mot 1, mot 2, ...), par défaut 'input/bd_mots_enonces.csv'
  --directory DIRECTORY, -d DIRECTORY
                        dossier des fichiers de sortie, par défaut 'output'
  --unknown, -u         calcule avec les mot énoncés qui n'ont pas de concept/mot mère, par défaut 'False'
  --verbose, -v         niveau de verbosité de la sortie, utiliser -v pour le mode INFO -vv pour le mode DEBUG
```
