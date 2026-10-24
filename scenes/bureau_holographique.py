"""Bureau holographique construit à partir de ressources de la bibliothèque (Kenney, Poly Haven), matériaux Mira.
La sélection vient de assets/selection_bureau.json (écrite par la mission 1). Ressource absente → le contrôle qualité bloque."""
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
import bpy  # noqa: E402
from bibliotheque import cameras, eclairages, environnements, execution, geonodes, import_assets, materiaux  # noqa: E402
from bibliotheque.palettes import PALETTES  # noqa: E402

SEL = json.load(open(os.path.join(RACINE, "assets", "selection_bureau.json")))
META = {"nom": "bureau_holographique", "duree_s": 5, "fps": 24, "personnages": [], "audio": None,
        "fond": PALETTES["univers"]["fond_nuit"], "format": "9:16", "assets": [x["id"] for x in SEL["objets"]] + [SEL.get("hdri", {}).get("id")]}


def placer(role, chemin, hauteur, pos, rot=0.0, style="sombre_aretes"):
    objs = import_assets.importer(os.path.join(RACINE, chemin))
    import_assets.adapter_materiaux(objs, style, "mira")
    return import_assets.regrouper(objs, role, hauteur, pos, rot)


def construire(meta):
    D, fps = meta["duree_s"], meta["fps"]
    environnements.sol(couleur_hex="#05080f")
    plateau_z = 0.75
    for x in SEL["objets"]:
        r = x["role"]; f = x["fichier"]
        if r == "bureau":
            placer(r, f, plateau_z, (0, 0, 0))
        elif r == "chaise":
            placer(r, f, 0.95, (0.0, 0.55, 0), 180)
        elif r == "ecran":
            placer(r, f, 0.42, (0, 0.12, plateau_z))
        elif r == "clavier":
            placer(r, f, 0.03, (0, -0.15, plateau_z))
        elif r == "souris":
            placer(r, f, 0.03, (0.28, -0.15, plateau_z))
        elif r == "lampe":
            placer(r, f, 0.45, (-0.55, 0.05, plateau_z))
        elif r == "plante":
            placer(r, f, 0.75, (0.95, 0.2, 0))
        elif r == "livres":
            placer(r, f, 0.12, (0.5, 0.1, plateau_z))
    # écrans holographiques flottants au-dessus du bureau
    for i, (x, rz) in enumerate(((-0.55, 0.35), (0.55, -0.35))):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, 0.05, 1.45), rotation=(1.45, 0, rz))
        e = bpy.context.object; e.name = f"holo_ecran{i}"; e.scale = (0.42, 0.26, 1)
        e.data.materials.append(materiaux.verre_ecran("ecran_cyan", PALETTES["mira"]["principal"], 1.6))
        geonodes.aretes_lumineuses(e, 0.004, materiaux.emission("bord_ecran", PALETTES["mira"]["lumiere"], 5))
    environnements.socle_holo(PALETTES["mira"]["principal"], rayons=(1.2, 1.35), hauteur=0.005)
    geonodes.etincelles("poussiere", centre=(0, 0, 1.2), rayon=1.6, densite=4, taille=0.004,
                        materiau=materiaux.emission("poussiere_cyan", PALETTES["mira"]["lumiere"], 8))
    cam, cible = cameras.creer(focale=32, cible_loc=(0, 0, 0.9), dof_fstop=4.0)
    cameras.arc(cam, D, fps, de_deg=-30, a_deg=25, distance=(3.6, 2.9), hauteur=(1.6, 1.75))
    h = SEL.get("hdri", {}).get("fichier")
    eclairages.monde(meta["fond"], 0.35, hdri=os.path.join(RACINE, h) if h else None, fond_visible=meta["fond"])
    eclairages.nuit_holo(cible, cle_hex="#2ce6ff", contre_hex="#8a3dff", intensite=0.7)


execution.lancer(construire, META)
