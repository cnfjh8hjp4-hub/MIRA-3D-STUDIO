"""Éclairages cinématographiques prêts à l'emploi."""
import math

import bpy

from .palettes import hex_vers_lineaire


def monde(couleur_hex="#04121a", force=1.0, hdri=None, rotation_deg=0):
    """Fond uni (couleur exacte) ou HDRI Poly Haven déjà téléchargée (chemin local)."""
    w = bpy.data.worlds.new("monde"); w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    bg = N["Background"]
    if hdri:
        env = N.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(hdri, check_existing=True)
        mp = N.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value[2] = math.radians(rotation_deg)
        tc = N.new("ShaderNodeTexCoord")
        L.new(tc.outputs["Generated"], mp.inputs["Vector"]); L.new(mp.outputs[0], env.inputs["Vector"])
        L.new(env.outputs["Color"], bg.inputs["Color"])
    else:
        bg.inputs["Color"].default_value = hex_vers_lineaire(couleur_hex)
    bg.inputs["Strength"].default_value = force
    bpy.context.scene.world = w
    return w


def _zone(nom, loc, cible, energie, couleur_hex, taille):
    ld = bpy.data.lights.new(nom, "AREA"); ld.energy = energie; ld.color = hex_vers_lineaire(couleur_hex)[:3]; ld.size = taille
    o = bpy.data.objects.new(nom, ld); o.location = loc; bpy.context.scene.collection.objects.link(o)
    t = o.constraints.new("TRACK_TO"); t.target = cible; t.track_axis = "TRACK_NEGATIVE_Z"; t.up_axis = "UP_Y"
    return o


def nuit_holo(cible, cle_hex="#8a3dff", contre_hex="#2ce6ff", chaud_hex="#ffb36b", intensite=1.0):
    """Clé douce colorée à gauche, contre-jour complémentaire derrière, touche chaude basse à droite."""
    return [_zone("cle", (-2.2, -2.4, 3.0), cible, 160 * intensite, cle_hex, 2.5),
            _zone("contre", (1.8, 2.2, 2.8), cible, 240 * intensite, contre_hex, 1.5),
            _zone("chaud", (1.6, -0.9, 0.6), cible, 35 * intensite, chaud_hex, 0.4)]


def trois_points(cible, couleur_hex="#ffffff", intensite=1.0):
    return [_zone("cle", (-2.5, -2.5, 2.8), cible, 300 * intensite, couleur_hex, 2.0),
            _zone("debouchage", (2.5, -2.0, 1.8), cible, 90 * intensite, couleur_hex, 3.0),
            _zone("contre", (0.5, 2.8, 3.0), cible, 200 * intensite, couleur_hex, 1.0)]


CATALOGUE = {"nuit_holo": nuit_holo, "trois_points": trois_points}
