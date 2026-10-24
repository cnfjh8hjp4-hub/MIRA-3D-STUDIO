"""Mouvements de caméra réutilisables. Toutes les fonctions prennent des durées en secondes."""
import math

import bpy


def creer(nom="camera", focale=40, cible_loc=(0, 0, 1.25), dof_fstop=None):
    cible = bpy.data.objects.new(f"{nom}_cible", None); cible.location = cible_loc
    bpy.context.scene.collection.objects.link(cible)
    cd = bpy.data.cameras.new(nom); cd.lens = focale
    cam = bpy.data.objects.new(nom, cd); bpy.context.scene.collection.objects.link(cam)
    tc = cam.constraints.new("TRACK_TO"); tc.target = cible; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
    if dof_fstop:
        cd.dof.use_dof = True; cd.dof.focus_object = cible; cd.dof.aperture_fstop = dof_fstop
    bpy.context.scene.camera = cam
    return cam, cible


def _cle(cam, t, loc, fps):
    cam.location = loc; cam.keyframe_insert("location", frame=1 + round(t * fps))


def arc(cam, duree, fps, de_deg=-35, a_deg=35, distance=(4.0, 3.1), hauteur=(1.45, 1.6), pas=10):
    """Arc de cercle autour de la cible, avec rapprochement progressif."""
    for i in range(pas + 1):
        u = i / pas; e = 0.5 - 0.5 * math.cos(math.pi * u)  # entrée et sortie en douceur
        a = math.radians(de_deg + (a_deg - de_deg) * e); d = distance[0] + (distance[1] - distance[0]) * e
        z = hauteur[0] + (hauteur[1] - hauteur[0]) * math.sin(math.pi * u)
        _cle(cam, duree * u, (d * math.sin(a), -d * math.cos(a), z), fps)


def travelling_avant(cam, duree, fps, de=4.2, a=2.6, hauteur=1.5, x=(0.0, 0.0)):
    for t, d, xx in ((0, de, x[0]), (duree, a, x[1])):
        _cle(cam, t, (xx, -d, hauteur), fps)


def orbite(cam, duree, fps, distance=3.5, hauteur=1.5, tours=0.25, pas=24):
    for i in range(pas + 1):
        a = 2 * math.pi * tours * i / pas
        _cle(cam, duree * i / pas, (distance * math.sin(a), -distance * math.cos(a), hauteur), fps)


def respiration_camera(cam, amplitude=0.01):
    """Léger flottement « caméra à l'épaule » via un modificateur de bruit sur les courbes."""
    if not (cam.animation_data and cam.animation_data.action):
        cam.keyframe_insert("location", frame=1)
    for fc in cam.animation_data.action.fcurves:
        n = fc.modifiers.new("NOISE"); n.scale = 40; n.strength = amplitude * 2


CATALOGUE = {"arc": arc, "travelling_avant": travelling_avant, "orbite": orbite}
