# Outil de calcul de cartes cognitives

Le programme existe en deux versions avec les mêmes fonctionnalités :

- CLI (Command Line Interface), `cli.py`
- GUI (Graphic User Interface), `gui.py`

Il prend deux entrées :

- une _base de données des mots énoncés_, dite _cartes cognitives_, au format CSV (séparé par `;`) encodé en UTF-8 à la structure suivante :
  - `identifiant; mot 1; mot 2; ...`. Les cartes peuvent avoir des longueurs différentes
  - le fichier par défaut est `input/bd_mots_enonces.csv`, voir l'exemple
- un _thésaurus_, dit aussi _ontologie_, qui aux mots énoncés fait correspondre un mot mère, dit aussi _concept_,  au format CSV (séparé par `;`) encodé en UTF-8 à la structure suivante :
  - `mot mère; mot énoncé`.
  - le fichier par défaut est `input/thesaurus.csv`, voir l'exemple

Pour une base de mots énoncés dont le nom de fichier est `$BD.csv`, le programme produit les fichiers résultats suivants :

- `$BD_occurences.csv` : pour chaque mot énoncé, le nombre de fois où il apparait dans la base
- `$BD_positions.csv` : pour chaque position, la liste des mots énoncés dans cette position et la liste de fois où ils y apparaissent
- `$BD_meres.csv` : les cartes où les mots énoncés sont remplacés par leur mots mères associés, dites _cartes mères_. Un option permet de remplacer, ou pas, les mots énoncés qui n'ont pas de mot mère
- `$BD_occurences_meres.csv` : idem `$BD_occurences.csv` mais avec les cartes mères
- `$BD_positions_meres.csv` : idem `$BD_positions.csv` mais avec les cartes mères

 La CLI a l'interface suivante :

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
La GUI fait la même chose mais avec une fenêtre.