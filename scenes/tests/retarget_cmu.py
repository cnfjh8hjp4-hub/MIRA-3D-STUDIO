"""Test du retargeting : un clip CMU (assets/selection_mouvement.json) appliqué au mannequin holographique."""
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RACINE)
import bpy  # noqa: E402
from bibliotheque import cameras, eclairages, environnements, execution, import_assets, retarget  # noqa: E402
from bibliotheque.palettes import PALETTES  # noqa: E402
from bibliotheque.personnages import mannequin_holo  # noqa: E402

SEL = json.load(open(os.path.join(RACINE, "assets", "selection_mouvement.json")))
META = {"nom": "retarget_cmu", "duree_s": 4, "fps": 24, "personnages": ["mira"], "audio": None,
        "fond": PALETTES["univers"]["fond_nuit"], "format": "9:16", "assets": [SEL["id"]]}


def construire(meta):
    P = mannequin_holo(palette="mira", aretes=False)
    objs = import_assets.importer(os.path.join(RACINE, SEL["fichier"]))
    arm = next(o for o in objs if o.type == "ARMATURE"); arm.hide_render = True; arm.hide_viewport = True
    n = retarget.appliquer(arm, P, nb_images=int(meta["duree_s"] * meta["fps"]), en_place=True)
    print("images retargetées :", n)
    environnements.socle_holo(PALETTES["mira"]["principal"], hauteur=0.29)
    cam, cible = cameras.creer(focale=40, cible_loc=(0, 0, 1.15))
    cameras.arc(cam, meta["duree_s"], meta["fps"], de_deg=-25, a_deg=10, distance=(4.0, 3.6))
    eclairages.monde(meta["fond"])


execution.lancer(construire, META)
