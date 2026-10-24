"""Arthemis parle (réplique S06, voix ElevenLabs fournie) : bec synchronisé sur la voix, clignements, tête vivante,
ailes qui frémissent, bibliothèque de nuit en bokeh, étincelles violettes. Personnage construit pièce par pièce."""
import math
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from bibliotheque import cameras, eclairages, environnements, execution, geonodes, materiaux, mouvements  # noqa: E402
from bibliotheque.palettes import PALETTES  # noqa: E402
from bibliotheque.personnages import arthemis  # noqa: E402

VOIX = os.path.join(RACINE, "scenes", "medias", "arthemis_s06.mp3")
META = {"nom": "arthemis_parle", "duree_s": 8.3, "fps": 24, "personnages": ["arthemis"], "audio": VOIX, "format": "9:16"}


def construire(meta):
    fps = meta["fps"]; D = meta["duree_s"]; nb = int(round(D * fps))
    P = arthemis.construire()
    environnements.sol(couleur_hex="#06040f")
    environnements.bokeh(34, couleurs=("#ffb36b", "#8a3dff", "#5a0cff", "#2ce6ff"), profondeur=(4.5, 8.5))
    geonodes.etincelles("etincelles", centre=(0, 0, 1.0), rayon=1.0, densite=8, taille=0.005,
                        materiau=materiaux.emission("etincelle_violette", PALETTES["arthemis"]["lumiere"], 10))
    # voix → bec
    try:
        from bibliotheque.visemes import enveloppe_audio
        env = enveloppe_audio(VOIX, fps)
    except Exception as e:
        print("voix illisible :", e); env = [0.0] * nb
    for f in range(nb):
        e = env[f] if f < len(env) else 0.0
        P["bec_inf"].rotation_euler = (math.radians(26 * e), 0, 0); P["bec_inf"].keyframe_insert("rotation_euler", frame=f + 1)
        t = f / fps
        P["tete"].rotation_euler = (math.radians(-2 + 5 * e + 1.2 * math.sin(t * 2.1)), math.radians(6 * math.sin(t * 0.6 + 0.5)),
                                    math.radians(9 * math.sin(t * 0.37)))
        P["tete"].keyframe_insert("rotation_euler", frame=f + 1)
    for t in (1.1, 3.8, 6.5):
        arthemis.cligner(P, t, fps)
    mouvements.respiration(P["corps"], D, fps, amplitude=0.015, vitesse=2.2)
    for cote, s in (("g", 1), ("d", -1)):
        a = P[f"aile_{cote}"]
        for t, ang in ((0, 0), (4.6, 0), (5.0, s * -9), (5.5, s * 3), (6.0, 0), (D, 0)):
            a.rotation_euler = (0, math.radians(ang), 0); a.keyframe_insert("rotation_euler", frame=1 + round(t * fps))
    mouvements.lisser([P["corps"], P["aile_g"], P["aile_d"]])
    cam, cible = cameras.creer(focale=50, cible_loc=(0, 0, 1.18), dof_fstop=2.2)
    cameras.travelling_avant(cam, D, fps, de=4.0, a=2.9, hauteur=1.32, x=(-0.25, 0.1))
    eclairages.monde(PALETTES["univers"]["nuit_profonde"], 1.0)
    eclairages.nuit_holo(cible, cle_hex="#8a3dff", contre_hex="#2ce6ff", intensite=0.8)


execution.lancer(construire, META)
