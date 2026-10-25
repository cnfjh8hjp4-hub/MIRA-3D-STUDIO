"""Retargeting de mouvements BVH (CMU…) vers les rigs Mira à pivots (bassin, buste, cou, tete, epaule_*, coude_*).

Méthode v1 :
- bassin, buste, cou, tête : rotation de l'os par rapport à sa pose de repos, exprimée dans les axes du monde
  (le BVH et nos rigs sont tous deux debout au repos) ;
- bras : direction de l'os (le BVH est en T, nos bras sont le long du corps au repos) : on oriente le segment
  vers la même direction ; la torsion du bras n'est pas transférée (limite connue) ;
- déplacement du bassin : facultatif (« en_place » garde le personnage sur place).
Statut : expérimental tant qu'un rendu contrôlé ne l'a pas validé."""
import bpy
from mathutils import Matrix, Quaternion, Vector

CORRESPONDANCE_CMU = {"bassin": ["Hips"], "buste": ["Spine1", "Spine", "LowerBack"], "cou": ["Neck1", "Neck"], "tete": ["Head"],
                      "epaule_g": ["LeftArm"], "coude_g": ["LeftForeArm"], "epaule_d": ["RightArm"], "coude_d": ["RightForeArm"]}
DIRECTION_REPOS = {"epaule_g": Vector((0, 0, -1)), "coude_g": Vector((0, 0, -1)), "epaule_d": Vector((0, 0, -1)), "coude_d": Vector((0, 0, -1))}
ORDRE = ["bassin", "buste", "cou", "tete", "epaule_g", "coude_g", "epaule_d", "coude_d"]


def _os(arm, noms):
    for n in noms:
        if n in arm.pose.bones:
            return arm.pose.bones[n]
    return None


def appliquer(arm, pivots, debut_bvh=None, nb_images=None, premiere_image=1, en_place=True, amplitude=1.0):
    """Copie le mouvement de l'armature BVH sur les pivots, image par image (images clés). Renvoie le nombre d'images."""
    sc = bpy.context.scene
    act = arm.animation_data.action
    a0, a1 = int(act.frame_range[0]), int(act.frame_range[1])
    debut = debut_bvh or a0
    nb = min(nb_images or (a1 - debut + 1), a1 - debut + 1)
    lies = {p: _os(arm, CORRESPONDANCE_CMU[p]) for p in ORDRE if p in pivots}
    lies = {p: b for p, b in lies.items() if b}
    mw = arm.matrix_world.to_quaternion()
    repos_world = {p: mw @ b.bone.matrix_local.to_quaternion() for p, b in lies.items()}
    hanches0 = None
    for i in range(nb):
        sc.frame_set(debut + i); bpy.context.view_layer.update()
        monde = {}
        for p in ORDRE:
            if p not in lies:
                continue
            b = lies[p]; piv = pivots[p]
            parent_q = monde.get(_parent(p, pivots), Quaternion())
            if p in DIRECTION_REPOS:
                d = (arm.matrix_world @ b.tail - arm.matrix_world @ b.head).normalized()
                q_monde = DIRECTION_REPOS[p].rotation_difference(d)
            else:
                pose_world = mw @ (b.matrix.to_quaternion())
                q_monde = pose_world @ repos_world[p].inverted()
            if amplitude != 1.0:
                q_monde = Quaternion().slerp(q_monde, amplitude)
            monde[p] = q_monde
            locale = parent_q.inverted() @ q_monde
            piv.rotation_mode = "QUATERNION"; piv.rotation_quaternion = locale
            piv.keyframe_insert("rotation_quaternion", frame=premiere_image + i)
        if "bassin" in lies and not en_place:
            h = arm.matrix_world @ lies["bassin"].head
            hanches0 = hanches0 or h.copy()
            pivots["bassin"].location = pivots["bassin"].location + (h - hanches0) * 0  # déplacement désactivé en v1
    return nb


def _parent(p, pivots):
    o = pivots[p].parent
    while o is not None:
        for k, v in pivots.items():
            if v is o and k in ORDRE:
                return k
        o = o.parent
    return None


def amplitude_mouvement(pivots):
    """Angle maximal (degrés) parcouru par chaque pivot animé : sert à vérifier qu'un mouvement a vraiment été transféré."""
    import math
    out = {}
    for nom, o in pivots.items():
        ad = o.animation_data
        if not (ad and ad.action):
            continue
        fcs = [fc for fc in ad.action.fcurves if fc.data_path == "rotation_quaternion"]
        if len(fcs) < 4:
            continue
        frames = sorted({int(k.co[0]) for k in fcs[0].keyframe_points})
        qs = [Quaternion([fcs[i].evaluate(f) for i in range(4)]).normalized() for f in frames]
        out[nom] = round(max(math.degrees(qs[0].rotation_difference(q).angle) for q in qs), 1)
    return out
