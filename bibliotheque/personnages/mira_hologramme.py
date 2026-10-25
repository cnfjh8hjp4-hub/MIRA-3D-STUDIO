"""Mira en hologramme, à partir du modèle 3D généré depuis son image OFFICIELLE (TRELLIS, licence MIT).
Statut : à valider par le propriétaire (modèle automatique : visage et mains simplifiés).
La texture d'origine sert de carte de luminosité (visage, cheveux, vêtements restent lisibles), teintée dans la
palette officielle de Mira. Squelette simple tête / buste pour l'animation. Effet d'apparition par balayage."""
import math
import os

import bpy
import numpy as np

from .. import import_assets
from ..palettes import PALETTES, hex_vers_lineaire

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELE = os.path.join(RACINE, "assets", "personnages", "mira_trellis.glb")
PAL = PALETTES["mira"]


def _materiau(img, hauteur, pal=PAL, plancher="#1a8fb0", nom="mira_holo", buste_uniforme=True):
    m = bpy.data.materials.new(nom); m.use_nodes = True; N, L = m.node_tree.nodes, m.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputMaterial"); tc = N.new("ShaderNodeTexCoord")
    tex = N.new("ShaderNodeTexImage"); tex.image = img; L.new(tc.outputs["UV"], tex.inputs["Vector"])
    bw = N.new("ShaderNodeRGBToBW"); L.new(tex.outputs["Color"], bw.inputs["Color"])
    ramp = N.new("ShaderNodeValToRGB"); cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = hex_vers_lineaire(plancher)  # pas de zones sombres « trouées »
    cr.elements[1].position = 0.9; cr.elements[1].color = hex_vers_lineaire(pal["lumiere"])
    e = cr.elements.new(0.4); e.color = hex_vers_lineaire(pal["principal"])
    # buste : luminosité uniforme (l'ombrage de la texture y créait des formes ambiguës) ; visage et cheveux gardent leur détail
    sepz = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sepz.inputs[0])
    bande = N.new("ShaderNodeMapRange"); bande.interpolation_type = "SMOOTHSTEP"
    bande.inputs["From Min"].default_value = hauteur * 0.80; bande.inputs["From Max"].default_value = hauteur * 0.84
    bande.inputs["To Min"].default_value = 1.0; bande.inputs["To Max"].default_value = 0.0; L.new(sepz.outputs["Z"], bande.inputs["Value"])
    bas = N.new("ShaderNodeMapRange"); bas.interpolation_type = "SMOOTHSTEP"  # le pantalon garde sa couleur sombre
    bas.inputs["From Min"].default_value = hauteur * 0.55; bas.inputs["From Max"].default_value = hauteur * 0.58
    L.new(sepz.outputs["Z"], bas.inputs["Value"])
    masque = N.new("ShaderNodeMath"); masque.operation = "MULTIPLY"
    L.new(bande.outputs["Result"], masque.inputs[0]); L.new(bas.outputs["Result"], masque.inputs[1])
    uni = N.new("ShaderNodeMix"); uni.data_type = "FLOAT"; uni.inputs["B"].default_value = 0.55
    if not buste_uniforme:
        masque.inputs[1].default_value = 0.0; L.remove(masque.inputs[1].links[0])
    L.new(masque.outputs[0], uni.inputs["Factor"]); L.new(bw.outputs["Val"], uni.inputs["A"])
    L.new(uni.outputs["Result"], ramp.inputs["Fac"])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
    rim = N.new("ShaderNodeMath"); rim.operation = "POWER"; rim.inputs[1].default_value = 2.0; L.new(lw.outputs["Facing"], rim.inputs[0])
    # lignes de balayage fines qui montent
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    wave = N.new("ShaderNodeTexWave"); wave.wave_type = "BANDS"; wave.bands_direction = "Z"; wave.inputs["Scale"].default_value = 60
    L.new(tc.outputs["Object"], wave.inputs["Vector"]); wave.inputs["Phase Offset"].driver_add("default_value").driver.expression = "-frame*0.3"
    scan = N.new("ShaderNodeMapRange"); scan.inputs["From Min"].default_value = 0.6; scan.inputs["To Min"].default_value = 0.85
    scan.inputs["To Max"].default_value = 1.2; L.new(wave.outputs["Fac"], scan.inputs["Value"])
    force = N.new("ShaderNodeMath"); force.operation = "MULTIPLY_ADD"; force.inputs[1].default_value = 1.6
    L.new(bw.outputs["Val"], force.inputs[0]); force.inputs[2].default_value = 0.5
    f2 = N.new("ShaderNodeMath"); f2.operation = "MULTIPLY_ADD"; f2.inputs[1].default_value = 2.2
    L.new(rim.outputs[0], f2.inputs[0]); L.new(force.outputs[0], f2.inputs[2])
    f3 = N.new("ShaderNodeMath"); f3.operation = "MULTIPLY"; L.new(f2.outputs[0], f3.inputs[0]); L.new(scan.outputs["Result"], f3.inputs[1])
    # apparition : tout ce qui est au-dessus du seuil est invisible, liseré lumineux au niveau du seuil
    seuil = N.new("ShaderNodeValue"); seuil.name = "apparition"; seuil.outputs[0].default_value = hauteur + 0.1
    diff = N.new("ShaderNodeMath"); diff.operation = "SUBTRACT"; L.new(seuil.outputs[0], diff.inputs[0]); L.new(sep.outputs["Z"], diff.inputs[1])
    visible = N.new("ShaderNodeMath"); visible.operation = "GREATER_THAN"; visible.inputs[1].default_value = 0.0; L.new(diff.outputs[0], visible.inputs[0])
    lis = N.new("ShaderNodeMapRange"); lis.inputs["From Min"].default_value = 0.0; lis.inputs["From Max"].default_value = 0.04
    lis.inputs["To Min"].default_value = 12.0; lis.inputs["To Max"].default_value = 0.0; lis.clamp = True; L.new(diff.outputs[0], lis.inputs["Value"])
    f4 = N.new("ShaderNodeMath"); f4.operation = "ADD"; L.new(f3.outputs[0], f4.inputs[0]); L.new(lis.outputs["Result"], f4.inputs[1])
    mixc = N.new("ShaderNodeMix"); mixc.data_type = "RGBA"; mixc.inputs["B"].default_value = hex_vers_lineaire(pal["lumiere"])
    L.new(rim.outputs[0], mixc.inputs["Factor"]); L.new(ramp.outputs["Color"], mixc.inputs["A"])
    em = N.new("ShaderNodeEmission"); L.new(mixc.outputs["Result"], em.inputs["Color"]); L.new(f4.outputs[0], em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    alpha = N.new("ShaderNodeMath"); alpha.operation = "MULTIPLY"; alpha.inputs[1].default_value = 0.97; L.new(visible.outputs[0], alpha.inputs[0])
    mix = N.new("ShaderNodeMixShader"); L.new(alpha.outputs[0], mix.inputs["Fac"]); L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    return m, seuil


def construire(hauteur=1.68, modele=MODELE, palette="mira", plancher="#1a8fb0", ratio_cou=0.835, nom="mira", buste_uniforme=None):
    pal = PALETTES[palette]
    objs = import_assets.importer(modele)
    meshes = [o for o in objs if o.type == "MESH"]
    img = next((n.image for o in meshes for ms in o.material_slots if ms.material and ms.material.use_nodes
                for n in ms.material.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM"); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1:
        bpy.ops.object.join()
    corps = bpy.context.view_layer.objects.active; corps.name = nom
    co = np.array([v.co[:] for v in corps.data.vertices])
    mn, mx = co.min(axis=0), co.max(axis=0); k = hauteur / (mx[2] - mn[2])
    co = (co - np.array([(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]])) * k
    for v, c in zip(corps.data.vertices, co):
        v.co = c
    corps.data.update(); bpy.ops.object.shade_smooth()
    # orientation : le visage doit regarder -Y (vers la caméra)
    m, seuil = _materiau(img, hauteur, pal, plancher, f"{nom}_holo", palette == "mira" if buste_uniforme is None else buste_uniforme)
    corps.data.materials.clear(); corps.data.materials.append(m)
    # squelette : buste et tête, poids lissés selon la hauteur
    cou = hauteur * ratio_cou
    def lisse(x, a, b):
        t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
    w_tete = lisse(co[:, 2], cou - 0.03, cou + 0.05); w_buste = lisse(co[:, 2], hauteur * 0.5, hauteur * 0.62) * (1 - w_tete)
    g = {n: corps.vertex_groups.new(name=n) for n in ("bassin", "buste", "tete")}
    for i in range(len(co)):
        for n, w in (("tete", w_tete[i]), ("buste", w_buste[i]), ("bassin", 1 - w_tete[i] - w_buste[i])):
            if w > 1e-3:
                g[n].add([i], float(w), "REPLACE")
    bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.object; arm.name = f"{nom}_squelette"
    bpy.ops.object.mode_set(mode="EDIT"); eb = arm.data.edit_bones
    b0 = eb[0]; b0.name = "bassin"; b0.head = (0, 0, hauteur * 0.5); b0.tail = (0, 0, hauteur * 0.6)
    b1 = eb.new("buste"); b1.head = b0.tail; b1.tail = (0, 0, cou); b1.parent = b0
    b2 = eb.new("tete"); b2.head = (0, 0, cou); b2.tail = (0, 0, hauteur); b2.parent = b1
    bpy.ops.object.mode_set(mode="POSE")
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")
    mod = corps.modifiers.new("squelette", "ARMATURE"); mod.object = arm
    return {"corps": corps, "squelette": arm, "os": arm.pose.bones, "seuil_apparition": seuil, "hauteur": hauteur}


def apparition(P, debut, duree, fps):
    s = P["seuil_apparition"].outputs[0]
    s.default_value = -0.05; s.keyframe_insert("default_value", frame=1 + round(debut * fps))
    s.default_value = P["hauteur"] + 0.1; s.keyframe_insert("default_value", frame=1 + round((debut + duree) * fps))
