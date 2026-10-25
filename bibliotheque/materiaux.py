"""Bibliothèque de matériaux réutilisables (Cycles et EEVEE).
Chaque fonction renvoie un matériau ; un même nom renvoie le même matériau (pas de doublons)."""
import bpy

from .palettes import hex_vers_lineaire


def _nouveau(nom):
    m = bpy.data.materials.get(nom)
    if m:
        return m, False
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, True


def _eevee_transparence(m, mode="BLENDED"):
    """EEVEE (4.2+) : rendu des transparences ; ignoré par Cycles."""
    for attr, val in (("surface_render_method", mode), ("use_transparency_overlap", True)):
        if hasattr(m, attr):
            try:
                setattr(m, attr, val)
            except Exception:
                pass


def emission(nom, couleur_hex, force=5.0):
    m, neuf = _nouveau(nom)
    if neuf:
        N, L = m.node_tree.nodes, m.node_tree.links
        e = N.new("ShaderNodeEmission"); e.inputs["Color"].default_value = hex_vers_lineaire(couleur_hex)
        e.inputs["Strength"].default_value = force
        o = N.new("ShaderNodeOutputMaterial"); L.new(e.outputs[0], o.inputs["Surface"])
    return m


def hologramme(nom, couleur_hex, bord_hex=None, force=2.5, opacite=0.55, balayage=True, constellations=False, plumes=0.0):
    """Hologramme : bords lumineux (Fresnel), centre transparent, lignes de balayage qui défilent,
    réseau de constellations facultatif."""
    m, neuf = _nouveau(nom)
    if not neuf:
        return m
    N, L = m.node_tree.nodes, m.node_tree.links
    out = N.new("ShaderNodeOutputMaterial")
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    fres = N.new("ShaderNodeMath"); fres.operation = "POWER"; fres.inputs[1].default_value = 1.6
    L.new(lw.outputs["Facing"], fres.inputs[0])
    force_n = N.new("ShaderNodeMath"); force_n.operation = "MULTIPLY_ADD"
    force_n.inputs[1].default_value = force * 2.4; force_n.inputs[2].default_value = force * 0.3
    L.new(fres.outputs[0], force_n.inputs[0])
    dernier = force_n.outputs[0]
    coord = N.new("ShaderNodeTexCoord")
    if balayage:
        vague = N.new("ShaderNodeTexWave"); vague.wave_type = "BANDS"; vague.bands_direction = "Z"
        vague.inputs["Scale"].default_value = 18; vague.inputs["Distortion"].default_value = 0
        L.new(coord.outputs["Object"], vague.inputs["Vector"])
        vague.inputs["Phase Offset"].driver_add("default_value").driver.expression = "frame*0.25"
        scan = N.new("ShaderNodeMapRange"); scan.inputs["From Min"].default_value = 0.7
        scan.inputs["To Min"].default_value = 0.8; scan.inputs["To Max"].default_value = 1.3
        L.new(vague.outputs["Fac"], scan.inputs["Value"])
        mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
        L.new(dernier, mul.inputs[0]); L.new(scan.outputs["Result"], mul.inputs[1]); dernier = mul.outputs[0]
    if constellations:
        vo = N.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 40
        L.new(coord.outputs["Object"], vo.inputs["Vector"])
        ligne = N.new("ShaderNodeMapRange"); ligne.inputs["From Max"].default_value = 0.012
        ligne.inputs["To Min"].default_value = 1.0; ligne.inputs["To Max"].default_value = 0.0; ligne.clamp = True
        L.new(vo.outputs["Distance"], ligne.inputs["Value"])
        add = N.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = force * 0.6
        L.new(ligne.outputs["Result"], add.inputs[0]); L.new(dernier, add.inputs[2]); dernier = add.outputs[0]
    if plumes:
        # plumes en écailles qui se chevauchent : rangées décalées, bord inférieur arrondi lumineux
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(coord.outputs["Object"], sep.inputs[0])
        def M(op, a_, b_=None, v=None):
            n = N.new("ShaderNodeMath"); n.operation = op
            for k_, x in enumerate((a_, b_)):
                if x is None:
                    continue
                if isinstance(x, (int, float)):
                    n.inputs[k_].default_value = x
                else:
                    L.new(x, n.inputs[k_])
            return n.outputs[0]
        f = 9.0 * plumes
        v = M("MULTIPLY", sep.outputs["Z"], -f * 1.25)                  # rangées vers le bas
        rang = M("FLOOR", v)
        decal = M("MULTIPLY", M("MODULO", rang, 2.0), 0.5)
        u = M("ADD", M("MULTIPLY", sep.outputs["X"], f), decal)
        du = M("SUBTRACT", M("FRACT", u), 0.5)
        dv = M("MULTIPLY", M("FRACT", v), 0.9)
        d = M("POWER", M("ADD", M("MULTIPLY", du, du), M("MULTIPLY", dv, dv)), 0.5)
        rim = N.new("ShaderNodeMapRange"); rim.inputs["From Min"].default_value = 0.34; rim.inputs["From Max"].default_value = 0.5
        rim.inputs["To Min"].default_value = 0.0; rim.inputs["To Max"].default_value = 1.0; rim.clamp = True
        L.new(d, rim.inputs["Value"])
        add2 = N.new("ShaderNodeMath"); add2.operation = "MULTIPLY_ADD"; add2.inputs[1].default_value = force * 1.4
        L.new(rim.outputs["Result"], add2.inputs[0]); L.new(dernier, add2.inputs[2]); dernier = add2.outputs[0]
    mixc = N.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    mixc.inputs["A"].default_value = hex_vers_lineaire(couleur_hex)
    mixc.inputs["B"].default_value = hex_vers_lineaire(bord_hex or couleur_hex)
    L.new(fres.outputs[0], mixc.inputs["Factor"])
    em = N.new("ShaderNodeEmission")
    L.new(mixc.outputs["Result"], em.inputs["Color"]); L.new(dernier, em.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    L.new(lw.outputs["Facing"], inv.inputs[1])
    fac = N.new("ShaderNodeMath"); fac.operation = "MULTIPLY_ADD"
    fac.inputs[1].default_value = -(1 - opacite); fac.inputs[2].default_value = 1.0; fac.use_clamp = True
    L.new(inv.outputs[0], fac.inputs[0])
    mix = N.new("ShaderNodeMixShader"); L.new(fac.outputs[0], mix.inputs["Fac"])
    L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    _eevee_transparence(m)
    return m


def sol_brillant(nom="sol_nuit", couleur_hex="#05080f", rugosite=0.18):
    """Sol sombre légèrement réfléchissant : renvoie les reflets des hologrammes."""
    m, neuf = _nouveau(nom)
    if neuf:
        N, L = m.node_tree.nodes, m.node_tree.links
        p = N.new("ShaderNodeBsdfPrincipled"); p.inputs["Base Color"].default_value = hex_vers_lineaire(couleur_hex)
        p.inputs["Roughness"].default_value = rugosite
        o = N.new("ShaderNodeOutputMaterial"); L.new(p.outputs[0], o.inputs["Surface"])
    return m


def verre_ecran(nom, couleur_hex, force=1.2):
    """Écran flottant : verre teinté + émission légère (bureaux holographiques)."""
    m, neuf = _nouveau(nom)
    if neuf:
        N, L = m.node_tree.nodes, m.node_tree.links
        e = N.new("ShaderNodeEmission"); e.inputs["Color"].default_value = hex_vers_lineaire(couleur_hex)
        e.inputs["Strength"].default_value = force
        t = N.new("ShaderNodeBsdfTransparent")
        mx = N.new("ShaderNodeMixShader"); mx.inputs["Fac"].default_value = 0.35
        L.new(t.outputs[0], mx.inputs[1]); L.new(e.outputs[0], mx.inputs[2])
        o = N.new("ShaderNodeOutputMaterial"); L.new(mx.outputs[0], o.inputs["Surface"])
        _eevee_transparence(m)
    return m


CATALOGUE = {"emission": emission, "hologramme": hologramme, "sol_brillant": sol_brillant, "verre_ecran": verre_ecran}
