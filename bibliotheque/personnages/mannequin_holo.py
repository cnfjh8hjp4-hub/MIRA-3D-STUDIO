"""Personnage holographique stylisé en primitives, avec hiérarchie de pivots :
bassin → buste → cou → tête (yeux) ; buste → épaules → coude. Arêtes lumineuses en Geometry Nodes."""
import bpy

from .. import geonodes, materiaux
from ..palettes import PALETTES


def _pivot(nom, loc, parent=None):
    o = bpy.data.objects.new(nom, None); bpy.context.scene.collection.objects.link(o)
    if parent:
        p = parent.matrix_world.translation
        o.parent = parent; o.location = (loc[0] - p.x, loc[1] - p.y, loc[2] - p.z)
    else:
        o.location = loc
    bpy.context.view_layer.update()
    return o


def construire(palette="mira", aretes=True):
    pal = PALETTES[palette]
    holo = materiaux.hologramme(f"holo_{palette}", pal["principal"], pal["lumiere"], force=1.3, opacite=0.45)
    fil = materiaux.emission(f"fil_{palette}", pal["principal"], 2.2)
    yeux = materiaux.emission(f"yeux_{palette}", "#e8ffff", 14.0)

    def piece(nom, loc, echelle, parent, avec_aretes=True):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=loc)
        o = bpy.context.object; o.name = nom; o.scale = echelle
        bpy.ops.object.transform_apply(scale=True)  # échelle appliquée : arêtes d'épaisseur uniforme
        bpy.ops.object.shade_smooth(); o.data.materials.append(holo)
        if aretes and avec_aretes:
            geonodes.aretes_lumineuses(o, 0.0035, fil)
        o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
        return o

    P = {}
    P["bassin"] = _pivot("bassin", (0, 0, 1.0))
    P["buste"] = _pivot("buste", (0, 0, 1.05), P["bassin"])
    P["cou"] = _pivot("cou", (0, 0, 1.55), P["buste"])
    P["tete"] = _pivot("tete", (0, 0, 1.68), P["cou"])
    P["epaule_g"] = _pivot("epaule_g", (0.27, 0, 1.47), P["buste"])
    P["epaule_d"] = _pivot("epaule_d", (-0.27, 0, 1.47), P["buste"])
    P["coude_d"] = _pivot("coude_d", (-0.30, 0, 1.18), P["epaule_d"])
    piece("torse", (0, 0, 1.28), (0.23, 0.15, 0.30), P["buste"])
    piece("hanches", (0, 0, 0.98), (0.19, 0.13, 0.13), P["bassin"])
    piece("cou_m", (0, 0, 1.60), (0.05, 0.05, 0.07), P["cou"], False)
    piece("tete_m", (0, 0, 1.78), (0.13, 0.135, 0.16), P["tete"])
    for x, nom in ((0.045, "oeil_g"), (-0.045, "oeil_d")):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, location=(x, -0.118, 1.80))
        o = bpy.context.object; o.name = nom; o.data.materials.append(yeux)
        o.parent = P["tete"]; o.matrix_parent_inverse = P["tete"].matrix_world.inverted()
    piece("bras_g", (0.31, 0, 1.30), (0.05, 0.05, 0.17), P["epaule_g"])
    piece("avbras_g", (0.33, 0, 1.00), (0.045, 0.045, 0.15), P["epaule_g"])
    piece("bras_d", (-0.31, 0, 1.30), (0.05, 0.05, 0.17), P["epaule_d"])
    piece("avbras_d", (-0.32, 0, 1.02), (0.045, 0.045, 0.15), P["coude_d"])
    piece("jambe_g", (0.10, 0, 0.62), (0.07, 0.07, 0.30), P["bassin"])
    piece("jambe_d", (-0.10, 0, 0.62), (0.07, 0.07, 0.30), P["bassin"])
    piece("pied_g", (0.10, -0.04, 0.32), (0.06, 0.09, 0.03), P["bassin"], False)
    piece("pied_d", (-0.10, -0.04, 0.32), (0.06, 0.09, 0.03), P["bassin"], False)
    return P
