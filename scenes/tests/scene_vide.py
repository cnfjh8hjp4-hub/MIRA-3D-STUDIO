"""Scène volontairement défectueuse (fond noir, caméra qui ne voit rien) : le Quality Inspector DOIT la refuser."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import bpy  # noqa: E402
from bibliotheque import cameras, eclairages, execution  # noqa: E402


def construire(meta):
    bpy.ops.mesh.primitive_cube_add(location=(0, 30, 0))  # derrière la caméra
    cam, cible = cameras.creer(cible_loc=(0, -10, 1.2))
    cam.location = (0, 0, 1.2)
    eclairages.monde("#000000", 0.0)


execution.lancer(construire, {"nom": "scene_vide", "duree_s": 1, "fps": 24, "personnages": [], "format": "9:16"})
