# Outil de calcul de cartes cognitives

La bibliothèque de base est dans le fichier [`cartes_cog.py`](cartes_cog.py).
Deux interfaces client existent avec les mêmes fonctionnalités :

- GUI (Graphic User Interface), [`gui.py`](gui.py) en TkInter
- CLI (Command Line Interface), [`cli.py`](cli.py)

## CHANGELOG

- 2021-09-01 :
  - support des deux cartes "la mine" et "la mine dans le futur"
  - valeurs par défaut des `filedialog` de la GUI
- 2021-07-26 :
  - première release

## Formats d'entrée

- une _base de données des mots énoncés_, dite _cartes cognitives_, au format CSV (séparé par `;`) encodé en UTF-8 à la structure suivante :
  - `identifiant; mot 1; mot 2; ...`. Les cartes peuvent avoir des longueurs différentes
  - **pas d'en-tête** dans la première ligne du fichier
- un _thésaurus_, dit aussi _ontologie_, qui aux mots énoncés fait correspondre un mot mère, dit aussi _concept_, au format CSV (séparé par `;`) encodé en UTF-8 à la structure suivante :
  - `mot mère; mot énoncé`.
  - **pas d'en-tête** dans la première ligne du fichier

## Calcul

Pour une base de mots énoncés dont le nom de fichier est `$BD.csv`, le programme produit les fichiers résultats suivants :

- `$BD_occurences.csv` : pour chaque mot énoncé, le nombre de fois où il apparait dans la base
- `$BD_positions.csv` : pour chaque position, la liste des mots énoncés dans cette position et la liste de fois où ils y apparaissent
- `$BD_meres.csv` : les cartes où les mots énoncés sont remplacés par leur mots mères associés, dites _cartes mères_. Un option permet de remplacer, ou pas, les mots énoncés qui n'ont pas de mot mère
- `$BD_inconnus.csv` : les mots des cartes qui n'apparaissent pas dans le thésaurus. Pour chaque mot inconnu, on donne les identifiants de carte où il apparaissent
- `$BD_occurences_meres.csv` : idem `$BD_occurences.csv` mais avec les cartes mères
- `$BD_positions_meres.csv` : idem `$BD_positions.csv` mais avec les cartes mères

## Entrées par défaut

Sans configuration, le calcul va être fait deux fois :

1. une fois sur les cartes _la mine_ avec comme entrées les cartes `input/cartes_cog_la_mine.csv` et le thésaurus `input/thesaurus_la_mine.csv`
2. une fois sur les cartes _la mine dans le futur_ avec comme entrées les cartes `input/cartes_cog_mine_futur.csv` et le thésaurus `input/thesaurus_mine_futur.csv`

Les exemples sont donnés dans le dossier [`input`](input/)
