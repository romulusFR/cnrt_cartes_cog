# pylint: disable = logging-fstring-interpolation
"""Interface ligne de commandes de gestion de cartes cognitives"""

__author__ = "Romuald Thion"

import argparse
from pathlib import Path
import logging
import sys
from cog_maps import (
    CM_LA_MINE_FILENAME,
    THESAURUS_FILENAME,
    WEIGHTS_MAP_FILENAME,
    OUTPUT_DIR,
    generate_results,
)

logging.basicConfig()
logger = logging.getLogger("COGNITIVE_MAP")


def get_parser():
    """Configuration de argparse pour les options deligne de commandes"""
    res = argparse.ArgumentParser(description="Outil de traitement des cartes cognitives")
    res.add_argument(
        "--maps",
        "-m",
        action="store",
        default=CM_LA_MINE_FILENAME,
        help=f"fichier csv des cartes cognitives, au format (id; mot 1; mot 2, ...), par défaut '{CM_LA_MINE_FILENAME}'",
    )
    res.add_argument(
        "--thesaurus",
        "-t",
        action="store",
        default=THESAURUS_FILENAME,
        help=f"fichier csv de description de l'ontologie, au format (concept; mot énoncé), par défaut '{THESAURUS_FILENAME}'",
    )
    res.add_argument(
        "--weights",
        "-w",
        action="store",
        default=WEIGHTS_MAP_FILENAME,
        help=f"fichier csv des pondérations par position, au format (pos; poids A; poids B, ...), par défaut '{WEIGHTS_MAP_FILENAME}'",
    )
    res.add_argument(
        "--output",
        "-o",
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

    Path(args.output).mkdir(parents=True, exist_ok=True)

    if not Path(args.maps).is_file():
        logger.critical(f"Le fichier {args.maps} est introuvable")
        sys.exit(1)
    if not Path(args.thesaurus).is_file():
        logger.critical(f"Le fichier {args.thesaurus} est introuvable")
        sys.exit(1)
    if not Path(args.weights).is_file():
        logger.critical(f"Le fichier {args.weights} est introuvable")
        sys.exit(1)

    generate_results(args.output, args.maps, args.thesaurus, args.weights, args.unknown)
