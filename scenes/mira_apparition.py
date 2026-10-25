"""Mira apparaît en hologramme (balayage de bas en haut), tourne la tête vers nous, respire ; la caméra se rapproche
jusqu'au cadrage épaules. Modèle : TRELLIS depuis son image officielle (à valider)."""
import math
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from bibliotheque import cameras, eclairages, environnements, execution, geonodes, materiaux  # noqa: E402
from bibliotheque.palettes import PALETTES  # noqa: E402
from bibliotheque.personnages import mira_hologramme  # noqa: E402

META = {"nom": "mira_apparition", "duree_s": 6, "fps": 24, "personnages": ["mira"], "audio": None,
        "fond": PALETTES["univers"]["fond_nuit"], "format": "9:16"}


def construire(meta):
    D, fps = meta["duree_s"], meta["fps"]
    P = mira_hologramme.construire()
    mira_hologramme.apparition(P, 0.2, 1.6, fps)
    os_ = P["os"]
    for t, (x, z) in ((0, (4, -25)), (1.8, (4, -25)), (2.8, (-3, 0)), (4.2, (-6, 6)), (D, (-2, 0))):
        os_["tete"].rotation_euler = (math.radians(x), 0, math.radians(z)); os_["tete"].keyframe_insert("rotation_euler", frame=1 + round(t * fps))
    for i in range(int(D / 0.25) + 1):
        t = i * 0.25; os_["buste"].rotation_euler = (math.radians(1.2 * math.sin(t * 2.3)), 0, math.radians(2 * math.sin(t * 0.6)))
        os_["buste"].keyframe_insert("rotation_euler", frame=1 + round(t * fps))
    environnements.sol(couleur_hex="#05080f")
    environnements.socle_holo(PALETTES["mira"]["principal"], rayons=(0.35, 0.48, 0.6), hauteur=0.005)
    environnements.bokeh(26, couleurs=("#2ce6ff", "#8a3dff", "#ffb36b"))
    geonodes.etincelles("etincelles", centre=(0, 0, 1.0), rayon=0.9, densite=6, taille=0.004,
                        materiau=materiaux.emission("etincelle_cyan", PALETTES["mira"]["lumiere"], 9))
    cam, cible = cameras.creer(focale=50, cible_loc=(0, 0, 0.95), dof_fstop=2.4)
    for t, loc, c in ((0, (0.0, -4.6, 1.0), (0, 0, 0.95)), (2.0, (0.1, -4.0, 1.2), (0, 0, 1.1)), (D, (0.25, -1.6, 1.5), (0, 0, 1.45))):
        cam.location = loc; cam.keyframe_insert("location", frame=1 + round(t * fps))
        cible.location = c; cible.keyframe_insert("location", frame=1 + round(t * fps))
    eclairages.monde(meta["fond"], 1.0)


execution.lancer(construire, META)
