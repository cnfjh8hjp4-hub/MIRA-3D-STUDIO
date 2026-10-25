"""Variante B d'Arthemis : modèle généré depuis son image officielle (TRELLIS, MIT) traité en hologramme violet,
pour comparer avec la version construite pièce par pièce. Tête animée ; bec et paupières non séparés (limite)."""
import math
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from bibliotheque import cameras, eclairages, environnements, execution, geonodes, materiaux  # noqa: E402
from bibliotheque.palettes import PALETTES  # noqa: E402
from bibliotheque.personnages import mira_hologramme  # noqa: E402

META = {"nom": "arthemis_holo_b", "duree_s": 5, "fps": 24, "personnages": ["arthemis"], "audio": None, "format": "9:16"}


def construire(meta):
    D, fps = meta["duree_s"], meta["fps"]
    P = mira_hologramme.construire(hauteur=1.45, modele=os.path.join(RACINE, "assets", "personnages", "arthemis_trellis.glb"),
                                   palette="arthemis", plancher="#3a12a0", ratio_cou=0.6, nom="arthemis")
    mira_hologramme.apparition(P, 0.1, 1.2, fps)
    t_ = P["os"]["tete"]
    for t, (x, y, z) in ((0, (0, 0, 0)), (1.6, (0, 0, 0)), (2.4, (-4, 6, 18)), (3.4, (3, -4, -10)), (D, (0, 0, 0))):
        t_.rotation_euler = (math.radians(x), math.radians(y), math.radians(z)); t_.keyframe_insert("rotation_euler", frame=1 + round(t * fps))
    environnements.sol(couleur_hex="#06040f")
    environnements.bokeh(30, couleurs=("#ffb36b", "#8a3dff", "#5a0cff", "#2ce6ff"), profondeur=(4.5, 8.5))
    geonodes.etincelles("etincelles", centre=(0, 0, 0.9), rayon=0.9, densite=6, taille=0.005,
                        materiau=materiaux.emission("etincelle_violette", PALETTES["arthemis"]["lumiere"], 10))
    cam, cible = cameras.creer(focale=50, cible_loc=(0, 0, 0.85), dof_fstop=2.2)
    cameras.travelling_avant(cam, D, fps, de=4.0, a=3.0, hauteur=1.05, x=(-0.2, 0.1))
    eclairages.monde(PALETTES["univers"]["nuit_profonde"], 1.0)


execution.lancer(construire, META)
