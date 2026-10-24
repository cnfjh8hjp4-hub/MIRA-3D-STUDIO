"""Démo MIRA 3D STUDIO (5 s) : personnage holographique stylisé, tête et corps animés, caméra mobile,
matériaux cyan lumineux, étincelles et anneaux en Geometry Nodes, fond bleu nuit #04121a.

Ne se lance pas seule : passe par le Render Manager →  ./studio produire scenes/demo_hologramme.py"""
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from bibliotheque import cameras, eclairages, environnements, execution, geonodes, materiaux, mouvements  # noqa: E402
from bibliotheque.palettes import PALETTES  # noqa: E402
from bibliotheque.personnages import mannequin_holo  # noqa: E402

META = {"nom": "demo_hologramme", "duree_s": 5, "fps": 24, "personnages": ["mira"], "audio": None,
        "fond": PALETTES["univers"]["fond_nuit"], "format": "9:16"}


def construire(meta):
    D, fps = meta["duree_s"], meta["fps"]
    P = mannequin_holo(palette="mira")
    environnements.socle_holo(PALETTES["mira"]["principal"], hauteur=0.29)
    geonodes.etincelles("etincelles", centre=(0, 0, 1.2), rayon=1.1, densite=30, taille=0.007,
                        materiau=materiaux.emission("etincelle_cyan", PALETTES["mira"]["lumiere"], 18))
    # animation
    mouvements.regard(P["tete"], fps, [(0, (0, 0, 0)), (1.0, (-6, 0, 28)), (2.0, (8, 0, 28)), (2.6, (-4, 0, 28)),
                                       (3.4, (2, 6, -22)), (4.3, (-3, 0, -5)), (D, (0, 0, 0))])
    mouvements.regard(P["buste"], fps, [(0, (0, 0, 0)), (1.2, (3, -3, 10)), (2.5, (-2, 3, 4)), (3.8, (3, 2, -12)), (D, (0, 0, 0))])
    mouvements.respiration(P["buste"], D, fps)
    mouvements.balancement(P["bassin"], D, fps)
    mouvements.salut(P["epaule_d"], P["coude_d"], 1.6, D, fps)
    mouvements.regard(P["epaule_g"], fps, [(0, (0, 0, 0)), (2.5, (0, 8, 0)), (D, (0, 0, 0))])
    mouvements.lisser(P.values())
    # caméra mobile et lumière
    cam, cible = cameras.creer(focale=40, cible_loc=(0, 0, 1.25))
    cameras.arc(cam, D, fps, de_deg=-35, a_deg=35, distance=(4.0, 3.1), hauteur=(1.45, 1.6))
    eclairages.monde(meta["fond"])


execution.lancer(construire, META)
