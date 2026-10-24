"""Bureaux et environnements réutilisables."""
import random

import bpy

from . import geonodes, materiaux


def socle_holo(couleur_hex="#2ce6ff", rayons=(0.45, 0.62, 0.8), hauteur=0.0):
    fil = materiaux.emission(f"anneau_{couleur_hex}", couleur_hex, 6.0)
    return [geonodes.anneau_scan(f"anneau{i}", rayon=r, epaisseur=0.006 + 0.002 * i, hauteur=hauteur,
                                 tours_par_s=0.05 * (1 if i % 2 else -1) * (1 + i * 0.3), materiau=fil)
            for i, r in enumerate(rayons)]


def sol(taille=14, couleur_hex="#05080f"):
    bpy.ops.mesh.primitive_plane_add(size=taille, location=(0, 0, 0))
    o = bpy.context.object; o.name = "sol"; o.data.materials.append(materiaux.sol_brillant(couleur_hex=couleur_hex))
    return o


def bokeh(nombre=30, couleurs=("#ffb36b", "#8a3dff", "#2ce6ff"), profondeur=(5.5, 9.0), graine=7):
    """Lumières lointaines qui deviennent des bokeh avec la profondeur de champ."""
    rnd = random.Random(graine); objs = []
    for i in range(nombre):
        c = couleurs[i % len(couleurs)]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=rnd.uniform(0.05, 0.13), segments=12, ring_count=6,
                                             location=(rnd.uniform(-4.5, 4.5), rnd.uniform(*profondeur), rnd.uniform(0.3, 5)))
        o = bpy.context.object; o.name = f"bokeh{i}"; o.visible_shadow = False
        o.data.materials.append(materiaux.emission(f"bokeh_{c}", c, rnd.uniform(6, 16))); objs.append(o)
    return objs


def bureau_holo(couleur_hex="#2ce6ff", position=(0, 0.6, 0)):
    """Bureau minimal : plateau sombre à arêtes lumineuses et deux écrans flottants."""
    x, y, z = position
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z + 0.74)); plateau = bpy.context.object; plateau.name = "bureau"
    plateau.scale = (0.8, 0.35, 0.02); bpy.ops.object.transform_apply(scale=True)
    plateau.data.materials.append(materiaux.sol_brillant("bureau_noir", "#0a0f1a", 0.25))
    geonodes.aretes_lumineuses(plateau, 0.004, materiaux.emission(f"arete_{couleur_hex}", couleur_hex, 5))
    ecrans = []
    for i, dx in enumerate((-0.35, 0.35)):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x + dx, y + 0.1, z + 1.15), rotation=(1.45, 0, -0.25 * (1 if dx < 0 else -1)))
        e = bpy.context.object; e.name = f"ecran{i}"; e.scale = (0.32, 0.2, 1)
        e.data.materials.append(materiaux.verre_ecran(f"ecran_{couleur_hex}", couleur_hex)); ecrans.append(e)
    return plateau, ecrans


CATALOGUE = {"socle_holo": socle_holo, "sol": sol, "bokeh": bokeh, "bureau_holo": bureau_holo}
