"""Arthemis, construite pièce par pièce d'après sa planche officielle (references/arthemis/) :
chouette debout de lumière violette, grands yeux lavande à pupille sombre, aigrettes en V, rameaux de feuilles
de chaque côté de la tête, poitrail en écailles de plumes, ailes repliées, serres.
Chaque partie qui bouge est séparée : paupières, bec inférieur, tête, ailes. Pivots :
corps → tete → (oeil_g, oeil_d, paupiere_g, paupiere_d, bec_inf) ; corps → aile_g, aile_d."""
import math

import bmesh
import bpy

from .. import materiaux
from ..palettes import PALETTES

PAL = PALETTES["arthemis"]


def _lier(o, parent):
    o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()


def _pivot(nom, loc, parent=None):
    o = bpy.data.objects.new(nom, None); bpy.context.scene.collection.objects.link(o)
    o.location = loc; bpy.context.view_layer.update()
    if parent:
        _lier(o, parent)
    return o


def _sphere(nom, loc, echelle, mat, parent, rot=(0, 0, 0), seg=32, lisse=True, subdiv=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc, rotation=rot)
    o = bpy.context.object; o.name = nom; o.scale = echelle
    bpy.ops.object.transform_apply(scale=True)
    if lisse:
        bpy.ops.object.shade_smooth()
    if subdiv:
        o.modifiers.new("lisse", "SUBSURF").levels = subdiv
    o.data.materials.append(mat); _lier(o, parent)
    return o


def _demi_sphere(nom, loc, rayon, mat, parent):
    """Paupière : demi-sphère supérieure, pivot au centre de l'œil."""
    me = bpy.data.meshes.new(nom); o = bpy.data.objects.new(nom, me); bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=rayon)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context="VERTS")
    bm.to_mesh(me); bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    o.location = loc; me.materials.append(mat); bpy.context.view_layer.update(); _lier(o, parent)
    return o


def _cone(nom, loc, r1, r2, prof, rot, mat, parent):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=r1, radius2=r2, depth=prof, location=loc, rotation=rot)
    o = bpy.context.object; o.name = nom; bpy.ops.object.shade_smooth(); o.data.materials.append(mat); _lier(o, parent)
    return o


def construire(echelle=1.0):
    corps_m = materiaux.hologramme("arthemis_corps", PAL["principal"], PAL["lumiere"], force=1.1, opacite=0.75,
                                   balayage=False, constellations=True, plumes=1.0)
    clair_m = materiaux.hologramme("arthemis_clair", "#8f5bff", PAL["lumiere"], force=1.5, opacite=0.8,
                                   balayage=False, constellations=True, plumes=1.6)
    lumi_m = materiaux.emission("arthemis_lumiere", PAL["lumiere"], 4.0)
    bec_m = materiaux.emission("arthemis_bec", "#b98cff", 2.2)
    iris_m = materiaux.emission("arthemis_iris", "#cdb2ff", 6.0)
    pupille_m = materiaux.emission("arthemis_pupille", "#12042a", 0.4)
    globe_m = materiaux.emission("arthemis_globe", "#2a0a66", 1.5)
    reflet_m = materiaux.emission("arthemis_reflet", "#ffffff", 25.0)

    P = {}
    P["racine"] = _pivot("arthemis", (0, 0, 0))
    P["corps"] = _pivot("corps", (0, 0, 0.55), P["racine"])
    P["tete"] = _pivot("tete", (0, 0.0, 1.16), P["corps"])
    # corps : œuf effilé vers le haut, poitrail clair, queue
    c = _sphere("corps_m", (0, 0, 0.70), (0.40, 0.36, 0.56), corps_m, P["corps"], subdiv=1)
    t = c.modifiers.new("effile", "SIMPLE_DEFORM"); t.deform_method = "TAPER"; t.factor = -0.35; t.deform_axis = "Z"
    _sphere("poitrail", (0, -0.20, 0.72), (0.29, 0.16, 0.42), clair_m, P["corps"], subdiv=1)
    _sphere("queue", (0, 0.22, 0.22), (0.16, 0.10, 0.20), corps_m, P["corps"], rot=(math.radians(-25), 0, 0))
    # tête, disques faciaux
    _sphere("tete_m", (0, 0, 1.38), (0.37, 0.33, 0.32), corps_m, P["tete"], subdiv=1)
    for s in (1, -1):
        _sphere(f"disque_{'g' if s > 0 else 'd'}", (s * 0.125, -0.235, 1.39), (0.155, 0.08, 0.15), clair_m, P["tete"])
    # yeux (globe sombre, iris lavande lumineux, pupille, reflet) + paupières mobiles
    for s, cote in ((1, "g"), (-1, "d")):
        x = s * 0.125; centre = (x, -0.29, 1.41)
        oeil = _pivot(f"oeil_{cote}", centre, P["tete"])
        _sphere(f"globe_{cote}", centre, (0.088, 0.088, 0.088), globe_m, oeil)
        _sphere(f"iris_{cote}", (x, -0.355, 1.41), (0.068, 0.03, 0.068), iris_m, oeil)
        _sphere(f"pupille_{cote}", (x, -0.375, 1.41), (0.034, 0.016, 0.034), pupille_m, oeil)
        _sphere(f"reflet_{cote}", (x + s * -0.02, -0.392, 1.435), (0.009, 0.006, 0.009), reflet_m, oeil, seg=12)
        pa = _demi_sphere(f"paupiere_{cote}", centre, 0.094, corps_m, P["tete"])
        pa.rotation_euler = (math.radians(-35), 0, 0)
        P[f"paupiere_{cote}"] = pa; P[f"oeil_{cote}"] = oeil
        # aigrettes en V au-dessus des yeux
        for k, (dx, dz, ang, lg) in enumerate(((0.03, 0.17, 30, 0.17), (0.09, 0.19, 42, 0.20), (0.15, 0.16, 55, 0.15))):
            _sphere(f"aigrette_{cote}{k}", (s * (0.06 + dx), -0.16, 1.40 + dz), (0.022, 0.012, lg), lumi_m, P["tete"],
                    rot=(math.radians(-20), math.radians(s * ang), 0), seg=16)
        # rameaux de feuilles sur les côtés de la tête
        for k in range(5):
            a = math.radians(-40 + k * 22)
            _sphere(f"feuille_{cote}{k}", (s * (0.36 + 0.05 * math.cos(a)), -0.02 + 0.06 * k * 0.3, 1.40 + 0.13 * math.sin(a)),
                    (0.012, 0.042, 0.075), lumi_m, P["tete"], rot=(0, math.radians(s * (20 + k * 12)), 0), seg=12)
    # bec : partie haute fixe, partie basse articulée
    _cone("bec_sup", (0, -0.335, 1.325), 0.045, 0.0, 0.12, (math.radians(150), 0, 0), bec_m, P["tete"])
    P["bec_inf"] = _pivot("bec_inf", (0, -0.31, 1.31), P["tete"])
    _cone("bec_inf_m", (0, -0.325, 1.285), 0.03, 0.0, 0.06, (math.radians(160), 0, 0), bec_m, P["bec_inf"])
    # ailes repliées, articulées à l'épaule
    for s, cote in ((1, "g"), (-1, "d")):
        P[f"aile_{cote}"] = _pivot(f"aile_{cote}", (s * 0.33, 0.02, 1.08), P["corps"])
        _sphere(f"aile_{cote}_m", (s * 0.40, 0.04, 0.68), (0.10, 0.25, 0.50), corps_m, P[f"aile_{cote}"],
                rot=(math.radians(-6), math.radians(s * -8), 0), subdiv=1)
        _sphere(f"remiges_{cote}", (s * 0.40, 0.14, 0.30), (0.07, 0.10, 0.22), clair_m, P[f"aile_{cote}"], rot=(math.radians(-15), 0, 0))
        # serres : trois doigts par patte
        for k, ang in enumerate((-25, 0, 25)):
            _cone(f"serre_{cote}{k}", (s * 0.12 + math.sin(math.radians(ang)) * 0.05, -0.22, 0.04), 0.02, 0.004, 0.11,
                  (math.radians(95), 0, math.radians(ang)), bec_m, P["corps"])
    if echelle != 1.0:
        P["racine"].scale = (echelle,) * 3
    return P


def cligner(P, t, fps, duree=0.18):
    """Clignement des deux yeux à l'instant t (secondes)."""
    for cote in ("g", "d"):
        pa = P[f"paupiere_{cote}"]
        for dt, ang in ((0, -35), (duree * 0.45, 92), (duree, -35)):
            pa.rotation_euler = (math.radians(ang), 0, 0); pa.keyframe_insert("rotation_euler", frame=1 + round((t + dt) * fps))
