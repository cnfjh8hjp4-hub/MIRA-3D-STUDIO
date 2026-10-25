"""Arthemis (variante B, modèle fidèle à sa planche) parle avec sa voix : bec synchronisé, clignements, tête vivante."""
import math
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from bibliotheque import cameras, eclairages, environnements, execution, geonodes, materiaux  # noqa: E402
from bibliotheque.palettes import PALETTES  # noqa: E402
from bibliotheque.personnages import arthemis_b  # noqa: E402

VOIX = os.path.join(RACINE, "scenes", "medias", "arthemis_s06.mp3")
META = {"nom": "arthemis_parle_b", "duree_s": 8.3, "fps": 24, "personnages": ["arthemis"], "audio": VOIX, "format": "9:16"}


def construire(meta):
    fps = meta["fps"]; D = meta["duree_s"]; nb = int(round(D * fps))
    P = arthemis_b.construire()
    t_ = P["os"]["tete"]
    try:
        from bibliotheque.visemes import enveloppe_audio
        env = enveloppe_audio(VOIX, fps)
    except Exception as e:
        print("voix illisible :", e); env = [0.0] * nb
    for f in range(nb):
        e = env[f] if f < len(env) else 0.0; t = f / fps
        P["bec_inf"].rotation_euler = (math.radians(24 * e), 0, 0); P["bec_inf"].keyframe_insert("rotation_euler", frame=f + 1)
        t_.rotation_euler = (math.radians(-1 + 4 * e + 1.2 * math.sin(t * 2.1)), math.radians(5 * math.sin(t * 0.6 + 0.5)),
                             math.radians(10 * math.sin(t * 0.37)))
        t_.keyframe_insert("rotation_euler", frame=f + 1)
    for t in (1.1, 3.8, 6.5):
        arthemis_b.cligner(P, t, fps)
    environnements.sol(couleur_hex="#06040f")
    environnements.bokeh(30, couleurs=("#ffb36b", "#8a3dff", "#5a0cff", "#2ce6ff"), profondeur=(4.5, 8.5))
    geonodes.etincelles("etincelles", centre=(0, 0, 0.9), rayon=0.9, densite=6, taille=0.005,
                        materiau=materiaux.emission("etincelle_violette", PALETTES["arthemis"]["lumiere"], 10))
    cam, cible = cameras.creer(focale=50, cible_loc=(0, 0, 0.95), dof_fstop=2.2)
    cameras.travelling_avant(cam, D, fps, de=3.6, a=2.5, hauteur=1.1, x=(-0.2, 0.1))
    eclairages.monde(PALETTES["univers"]["nuit_profonde"], 1.0)


execution.lancer(construire, META)
