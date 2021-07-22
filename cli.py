# pylint: disable = logging-fstring-interpolation
"""Interface ligne de commandes"""

__author__ = "Romuald Thion"

import argparse
from pathlib import Path
import logging
import sys
from cartes_cog import (
    CARTES_COG_FILE_DEFAULT,
    ONTOLOGIE_FILE_DEFAULT,
    OUTPUT_DIR,
    generate_results,
)

logging.basicConfig()
logger = logging.getLogger("COGNITIVE_MAP")


def get_parser():
    """Configuration de argparse pour les options deligne de commandes"""
    res = argparse.ArgumentParser(description="Outil de traitement des cartes cognitives")
    res.add_argument(
        "--ontology",
        "-o",
        action="store",
        default=ONTOLOGIE_FILE_DEFAULT,
        help=f"fichier csv de description de l'ontologie, au format (concept, mot énoncé), par défaut '{ONTOLOGIE_FILE_DEFAULT}'",
    )
    res.add_argument(
        "--cartes",
        "-c",
        action="store",
        default=CARTES_COG_FILE_DEFAULT,
        help=f"fichier csv des cartes cognitives, au format (id, mot 1, mot 2, ...), par défaut '{CARTES_COG_FILE_DEFAULT}'",
    )
    res.add_argument(
        "--directory",
        "-d",
        action="store",
        default=OUTPUT_DIR,
        help=f"dossier des fichiers de sortie, par défaut '{OUTPUT_DIR}'",
    )
    res.add_argument(
        "--unknown",
        "-u",
        action="store_true",
        default=False,
        help=f"calcule avec les mot énoncés qui n'ont pas de concept/mot mère, par défaut '{False}'",
    )
    res.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="niveau de verbosité de la sortie, utiliser -v pour le mode INFO -vv pour le mode DEBUG",
    )
    return res


# Programme principal de l'nterface ligne de commande
if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    # https://docs.python.org/3/library/logging.html#levels
    if args.verbose >= 2:
        LEVEL = logging.DEBUG
    elif args.verbose == 1:
        LEVEL = logging.INFO
    else:
        LEVEL = logging.WARNING

    logger.setLevel(LEVEL)

    logger.debug(args)
    if not Path(args.ontology).is_file():
        logger.critical(f"Le fichier {args.ontology} est introuvable")
        sys.exit(2)
    if not Path(args.cartes).is_file():
        logger.critical(f"Le fichier {args.cartes} est introuvable")
        sys.exit(2)

    generate_results(args.directory, args.cartes, args.ontology, args.unknown)
