# Interface CLI

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
