"""Arthemis variante B : modèle généré depuis son image officielle (TRELLIS, MIT) en hologramme violet,
+ yeux lumineux, paupières et bec inférieur ajoutés et articulés (placés automatiquement sur le modèle :
yeux = zones les plus claires de la texture en haut et à l'avant de la tête ; bec = pointe la plus avancée entre les yeux)."""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from .. import materiaux
from ..palettes import PALETTES
from . import mira_hologramme

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELE = os.path.join(RACINE, "assets", "personnages", "arthemis_trellis.glb")
PAL = PALETTES["arthemis"]


def _lum_par_sommet(obj, img):
    me = obj.data; uv = me.uv_layers.active.data
    w, h = img.size; px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    lum = 0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]
    som = np.zeros(len(me.vertices)); nb = np.zeros(len(me.vertices))
    for poly in me.polygons:
        for li in poly.loop_indices:
            u, v = uv[li].uv; vi = me.loops[li].vertex_index
            som[vi] += lum[min(h - 1, max(0, int(v * h))), min(w - 1, max(0, int(u * w)))]; nb[vi] += 1
    return som / np.maximum(nb, 1)


def _attacher(o, arm, os_nom):
    bpy.context.view_layer.update()  # sinon matrix_world n'a pas encore la position donnée (bug du bec aux pieds)
    mw = o.matrix_world.copy(); o.parent = arm; o.parent_type = "BONE"; o.parent_bone = os_nom
    bpy.context.view_layer.update(); o.matrix_world = mw


def _sphere(nom, loc, echelle, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=loc)
    o = bpy.context.object; o.name = nom; o.scale = echelle; bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth(); o.data.materials.append(mat); return o


def construire(hauteur=1.45):
    P = mira_hologramme.construire(hauteur=hauteur, modele=MODELE, palette="arthemis", plancher="#3a12a0", ratio_cou=0.6, nom="arthemis")
    corps, arm = P["corps"], P["squelette"]
    img = next(n.image for n in corps.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE")
    co = np.array([v.co[:] for v in corps.data.vertices]); lum = _lum_par_sommet(corps, img)
    zt = co[:, 2].max()
    tete = (co[:, 2] > zt * 0.63) & (co[:, 2] < zt * 0.75)  # sous les sourcils (zone la plus claire, à exclure)
    avant = co[:, 1] < np.percentile(co[tete, 1], 30)
    cand = np.where(tete & avant & (np.abs(co[:, 0]) > 0.03))[0]
    seuil = np.percentile(lum[cand], 85); clairs = cand[lum[cand] >= seuil]
    yeux = {}
    for cote, s in (("g", 1), ("d", -1)):
        c = clairs[np.sign(co[clairs, 0]) == s]
        if len(c) < 3:
            c = cand[np.sign(co[cand, 0]) == s]
        yeux[cote] = co[c].mean(axis=0)
    ecart = abs(yeux["g"][0] - yeux["d"][0]); r = max(0.03, min(0.065, ecart * 0.24))
    zy = (yeux["g"][2] + yeux["d"][2]) / 2
    m_bec = (np.abs(co[:, 0]) < ecart * 0.25) & (co[:, 2] < zy - r * 0.3) & (co[:, 2] > zy - r * 3)
    idx = np.where(m_bec)[0]; pointe = co[idx[np.argmin(co[idx, 1])]] if len(idx) else np.array([0, yeux["g"][1] - r, zy - 2 * r])
    print("yeux", yeux, "rayon", r, "bec", pointe, flush=True)
    iris_m = materiaux.emission("arthemis_b_iris", "#5a2cff", 1.2); clair_m = materiaux.emission("arthemis_b_iris_clair", "#b896ff", 1.1)
    pup_m = materiaux.emission("arthemis_b_pupille", "#0b0220", 0.2); ref_m = materiaux.emission("arthemis_b_reflet", "#ffffff", 8)
    pau_m = materiaux.hologramme("arthemis_b_paupiere", PAL["principal"], PAL["lumiere"], force=0.9, opacite=0.95, balayage=False)
    bec_m = materiaux.emission("arthemis_b_bec", "#b58cff", 1.4)
    for cote, s in (("g", 1), ("d", -1)):
        x, y, z = yeux[cote]; y -= r * 0.15
        objs = [_sphere(f"iris_{cote}", (x, y, z), (r, r * 0.35, r), iris_m),
                _sphere(f"iris_clair_{cote}", (x, y - r * 0.12, z), (r * 0.62, r * 0.25, r * 0.62), clair_m),
                _sphere(f"pupille_{cote}", (x, y - r * 0.22, z), (r * 0.42, r * 0.2, r * 0.42), pup_m),
                _sphere(f"reflet_{cote}", (x - s * r * 0.3, y - r * 0.3, z + r * 0.3), (r * 0.13, r * 0.08, r * 0.13), ref_m)]
        for o in objs:
            _attacher(o, arm, "tete")
        me = bpy.data.meshes.new(f"paupiere_{cote}"); pa = bpy.data.objects.new(f"paupiere_{cote}", me); bpy.context.scene.collection.objects.link(pa)
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=r * 1.12)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context="VERTS"); bm.to_mesh(me); bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(pau_m); pa.location = (x, y + r * 0.2, z); pa.rotation_euler = (math.radians(-40), 0, 0)
        _attacher(pa, arm, "tete"); P[f"paupiere_{cote}"] = pa
    # bec inférieur articulé sous la pointe du bec
    bec = bpy.data.objects.new("bec_inf", None); bpy.context.scene.collection.objects.link(bec)
    bec.location = (0, pointe[1] + r * 0.5, pointe[2] + r * 0.2); _attacher(bec, arm, "tete")
    bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=r * 0.38, radius2=0, depth=r * 0.8,
                                    location=(0, pointe[1] + r * 0.25, pointe[2] - r * 0.15), rotation=(math.radians(160), 0, 0))
    b = bpy.context.object; b.name = "bec_inf_m"; b.data.materials.append(bec_m); bpy.ops.object.shade_smooth()
    bpy.context.view_layer.update(); mw = b.matrix_world.copy(); b.parent = bec; bpy.context.view_layer.update(); b.matrix_world = mw
    P["bec_inf"] = bec; P["rayon_oeil"] = r
    return P


def cligner(P, t, fps, duree=0.18):
    for cote in ("g", "d"):
        pa = P[f"paupiere_{cote}"]
        for dt, ang in ((0, -40), (duree * 0.45, 92), (duree, -40)):
            pa.rotation_euler = (math.radians(ang), 0, 0); pa.keyframe_insert("rotation_euler", frame=1 + round((t + dt) * fps))
