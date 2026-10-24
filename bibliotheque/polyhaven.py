"""Ressources CC0 de Poly Haven DÉJÀ téléchargées (voir scripts/polyhaven.py) : aucune connexion depuis Blender."""
import glob
import os

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(RACINE, "cache", "polyhaven")


def chemin(type_, identifiant):
    f = sorted(glob.glob(os.path.join(CACHE, type_, f"{identifiant}_*")))
    if not f:
        raise FileNotFoundError(f"{type_} « {identifiant} » absente du cache : ./studio polyhaven {type_} {identifiant}")
    return f[0]


def hdri(identifiant):
    return chemin("hdris", identifiant)
