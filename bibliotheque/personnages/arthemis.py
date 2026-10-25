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
    corps_m = materiaux.hologramme("arthemis_corps", PAL["principal"], PAL["lumiere"], force=0.75, opacite=0.82,
                                   balayage=False, constellations=True, plumes=1.0)
    clair_m = materiaux.hologramme("arthemis_clair", "#7d45ff", PAL["lumiere"], force=0.95, opacite=0.85,
                                   balayage=False, constellations=False, plumes=1.5)
    plume_m = materiaux.hologramme("arthemis_plume", "#b08aff", "#efe2ff", force=1.3, opacite=0.6, balayage=False)
    bec_m = materiaux.emission("arthemis_bec", "#c7a3ff", 1.6)
    iris_m = materiaux.emission("arthemis_iris", "#7a3dff", 2.4)
    iris2_m = materiaux.emission("arthemis_iris_clair", "#b48cff", 1.8)
    serre_m = materiaux.emission("arthemis_serres", "#8a5cff", 1.0)
    pupille_m = materiaux.emission("arthemis_pupille", "#0b0220", 0.2)
    globe_m = materiaux.emission("arthemis_globe", "#2a0a66", 0.8)
    cerne_m = materiaux.emission("arthemis_cerne", "#2a0a66", 1.0)
    reflet_m = materiaux.emission("arthemis_reflet", "#ffffff", 18.0)

    P = {}
    P["racine"] = _pivot("arthemis", (0, 0, 0))
    P["corps"] = _pivot("corps", (0, 0, 0.55), P["racine"])
    P["tete"] = _pivot("tete", (0, 0.0, 1.08), P["corps"])
    # corps en œuf effilé, collerette qui relie la tête, poitrail en écailles, queue
    c = _sphere("corps_m", (0, 0, 0.68), (0.36, 0.33, 0.52), corps_m, P["corps"], subdiv=1)
    t = c.modifiers.new("effile", "SIMPLE_DEFORM"); t.deform_method = "TAPER"; t.factor = -0.25; t.deform_axis = "Z"
    _sphere("collerette", (0, -0.02, 1.08), (0.33, 0.29, 0.17), corps_m, P["corps"], subdiv=1)
    _sphere("poitrail", (0, -0.17, 0.70), (0.27, 0.15, 0.40), clair_m, P["corps"], subdiv=1)
    _sphere("queue", (0, 0.20, 0.20), (0.15, 0.09, 0.20), corps_m, P["corps"], rot=(math.radians(-25), 0, 0))
    # tête et disques faciaux
    _sphere("tete_m", (0, 0, 1.32), (0.39, 0.33, 0.33), corps_m, P["tete"], subdiv=1)
    for s in (1, -1):
        _sphere(f"disque_{'g' if s > 0 else 'd'}", (s * 0.12, -0.215, 1.31), (0.165, 0.075, 0.16), clair_m, P["tete"])
    for s, cote in ((1, "g"), (-1, "d")):
        x = s * 0.12; centre = (x, -0.265, 1.33)
        oeil = _pivot(f"oeil_{cote}", centre, P["tete"])
        _sphere(f"globe_{cote}", centre, (0.086, 0.086, 0.086), globe_m, oeil)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.092, minor_radius=0.008, location=(x, -0.30, 1.33), rotation=(math.radians(90), 0, 0))
        tor = bpy.context.object; tor.name = f"cerne_{cote}"; tor.data.materials.append(cerne_m); _lier(tor, P["tete"])
        _sphere(f"iris_{cote}", (x, -0.33, 1.33), (0.078, 0.026, 0.078), iris_m, oeil)
        _sphere(f"iris_clair_{cote}", (x, -0.343, 1.33), (0.05, 0.018, 0.05), iris2_m, oeil)
        _sphere(f"pupille_{cote}", (x, -0.355, 1.33), (0.033, 0.014, 0.033), pupille_m, oeil)
        _sphere(f"reflet_{cote}", (x + s * -0.022, -0.366, 1.355), (0.010, 0.006, 0.010), reflet_m, oeil, seg=12)
        pa = _demi_sphere(f"paupiere_{cote}", centre, 0.091, corps_m, P["tete"])
        pa.rotation_euler = (math.radians(-35), 0, 0)
        P[f"paupiere_{cote}"] = pa; P[f"oeil_{cote}"] = oeil
        # sourcils-aigrettes en V : grandes plumes qui partent au-dessus des yeux vers l'extérieur
        for k, (dx, dz, ang, lg, la) in enumerate(((0.05, 0.11, 38, 0.17, 0.05), (0.13, 0.13, 58, 0.15, 0.045))):
            _sphere(f"aigrette_{cote}{k}", (s * (0.04 + dx), -0.17, 1.39 + dz), (la, 0.014, lg), plume_m, P["tete"],
                    rot=(math.radians(-25), math.radians(s * ang), 0), seg=20)
        # rameau de feuilles sur le côté de la tête
        for k in range(4):
            a = math.radians(-20 + k * 28)
            _sphere(f"feuille_{cote}{k}", (s * (0.34 + 0.03 * k), 0.02, 1.30 + 0.16 * math.sin(a)),
                    (0.05, 0.012, 0.085), plume_m, P["tete"], rot=(0, math.radians(s * (35 + k * 18)), math.radians(s * 20)), seg=16)
    # bec : partie haute fixe, partie basse articulée
    _cone("bec_sup", (0, -0.31, 1.255), 0.05, 0.0, 0.13, (math.radians(150), 0, 0), bec_m, P["tete"])
    P["bec_inf"] = _pivot("bec_inf", (0, -0.285, 1.235), P["tete"])
    _cone("bec_inf_m", (0, -0.30, 1.21), 0.032, 0.0, 0.065, (math.radians(160), 0, 0), bec_m, P["bec_inf"])
    # ailes repliées contre le corps, articulées à l'épaule ; serres
    for s, cote in ((1, "g"), (-1, "d")):
        P[f"aile_{cote}"] = _pivot(f"aile_{cote}", (s * 0.28, 0.02, 1.02), P["corps"])
        _sphere(f"aile_{cote}_m", (s * 0.30, 0.03, 0.66), (0.09, 0.24, 0.50), corps_m, P[f"aile_{cote}"],
                rot=(math.radians(-5), math.radians(s * -6), math.radians(s * 12)), subdiv=1)
        _sphere(f"remiges_{cote}", (s * 0.28, 0.13, 0.28), (0.07, 0.10, 0.22), clair_m, P[f"aile_{cote}"], rot=(math.radians(-15), 0, 0))
        for k, ang in enumerate((-25, 0, 25)):
            _cone(f"serre_{cote}{k}", (s * 0.11 + math.sin(math.radians(ang)) * 0.05, -0.20, 0.04), 0.02, 0.004, 0.11,
                  (math.radians(95), 0, math.radians(ang)), serre_m, P["corps"])
    if echelle != 1.0:
        P["racine"].scale = (echelle,) * 3
    return P


def cligner(P, t, fps, duree=0.18):
    """Clignement des deux yeux à l'instant t (secondes)."""
    for cote in ("g", "d"):
        pa = P[f"paupiere_{cote}"]
        for dt, ang in ((0, -35), (duree * 0.45, 92), (duree, -35)):
            pa.rotation_euler = (math.radians(ang), 0, 0); pa.keyframe_insert("rotation_euler", frame=1 + round((t + dt) * fps))
