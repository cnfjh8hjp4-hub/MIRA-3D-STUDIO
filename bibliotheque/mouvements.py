"""Mouvements et expressions réutilisables pour des personnages à pivots (objets vides ou os en mode objet).
Temps en secondes ; chaque fonction pose ses propres images clés."""
import math


def _cle(obj, attr, t, v, fps):
    setattr(obj, attr, v); obj.keyframe_insert(attr, frame=1 + round(t * fps))


def respiration(buste, duree, fps, amplitude=0.025, vitesse=2.4):
    for i in range(int(duree / 0.25) + 1):
        t = i * 0.25; s = 1 + amplitude * math.sin(t * vitesse)
        _cle(buste, "scale", t, (s, s, 1), fps)


def balancement(bassin, duree, fps, base=(0, 0, 1.0), lateral=0.03, vertical=0.012):
    for i in range(int(duree / 0.25) + 1):
        t = i * 0.25
        _cle(bassin, "location", t, (base[0] + lateral * math.sin(t * 1.3), base[1], base[2] + vertical * math.sin(t * 2.6)), fps)


def regard(tete, fps, etapes):
    """etapes : [(t, (tangage_deg, roulis_deg, lacet_deg)), ...]"""
    for t, (x, y, z) in etapes:
        _cle(tete, "rotation_euler", t, (math.radians(x), math.radians(y), math.radians(z)), fps)


def hochement(tete, t, fps, amplitude_deg=8, base=(0, 0, 0)):
    for dt, k in ((0, 0), (0.18, 1), (0.36, -0.4), (0.55, 0)):
        _cle(tete, "rotation_euler", t + dt, (math.radians(base[0] + amplitude_deg * k), math.radians(base[1]), math.radians(base[2])), fps)


def salut(epaule, coude, debut, duree, fps):
    """Bras levé sur le côté (jamais derrière la tête), avant-bras qui oscille."""
    _cle(epaule, "rotation_euler", 0, (0, 0, 0), fps)
    _cle(epaule, "rotation_euler", debut, (math.radians(-20), math.radians(-115), 0), fps)
    _cle(epaule, "rotation_euler", duree, (math.radians(-20), math.radians(-115), 0), fps)
    _cle(coude, "rotation_euler", 0, (0, 0, 0), fps)
    t = debut
    while t <= duree:
        _cle(coude, "rotation_euler", t, (0, math.radians(-25 + 25 * math.sin((t - debut) * 7)), 0), fps)
        t += 0.15


def lisser(objets):
    for o in objets:
        if o.animation_data and o.animation_data.action:
            for fc in o.animation_data.action.fcurves:
                for k in fc.keyframe_points:
                    k.interpolation = "BEZIER"; k.easing = "AUTO"


EXPRESSIONS = {  # rotation de tête (deg) + intensité des yeux, pour les personnages simples
    "neutre": {"tete": (0, 0, 0), "yeux": 1.0}, "curieuse": {"tete": (-4, 8, 6), "yeux": 1.2},
    "reflexion": {"tete": (6, -5, -12), "yeux": 0.8}, "joie": {"tete": (-6, 0, 0), "yeux": 1.4},
}
