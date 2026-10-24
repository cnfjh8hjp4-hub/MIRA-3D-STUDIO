"""Effets holographiques et particules en Geometry Nodes (aucune simulation à recalculer : tout dépend du temps).
- etincelles : nuée de points lumineux qui dérivent autour d'une zone
- anneau_scan : anneau lumineux qui tourne (socle d'hologramme)
- aretes_lumineuses : remplace le modificateur Wireframe par des tubes lumineux le long des arêtes"""
import bpy


def _arbre(nom):
    ng = bpy.data.node_groups.new(nom, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    ent = ng.nodes.new("NodeGroupInput"); sor = ng.nodes.new("NodeGroupOutput")
    return ng, ent, sor


def _modif(obj, ng):
    m = obj.modifiers.new(ng.name, "NODES"); m.node_group = ng
    return m


def etincelles(nom, centre=(0, 0, 1.2), rayon=1.4, densite=40.0, taille=0.008, materiau=None, vitesse=0.15, graine=3):
    """Crée un objet porteur (sphère invisible) et y distribue des étincelles animées."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=rayon, location=centre)
    porteur = bpy.context.object; porteur.name = nom
    ng, ent, sor = _arbre(f"GN_{nom}")
    N, L = ng.nodes, ng.links
    dist = N.new("GeometryNodeDistributePointsOnFaces"); dist.inputs["Density"].default_value = densite
    dist.inputs["Seed"].default_value = graine
    L.new(ent.outputs[0], dist.inputs["Mesh"])
    temps = N.new("GeometryNodeInputSceneTime")
    pos = N.new("GeometryNodeInputPosition")
    mulT = N.new("ShaderNodeMath"); mulT.operation = "MULTIPLY"; mulT.inputs[1].default_value = vitesse
    L.new(temps.outputs["Seconds"], mulT.inputs[0])
    bruit = N.new("ShaderNodeTexNoise"); bruit.noise_dimensions = "4D"; bruit.inputs["Scale"].default_value = 0.8
    L.new(pos.outputs[0], bruit.inputs["Vector"]); L.new(mulT.outputs[0], bruit.inputs["W"])
    centrer = N.new("ShaderNodeVectorMath"); centrer.operation = "SUBTRACT"; centrer.inputs[1].default_value = (0.5, 0.5, 0.5)
    L.new(bruit.outputs["Color"], centrer.inputs[0])
    amp = N.new("ShaderNodeVectorMath"); amp.operation = "SCALE"; amp.inputs["Scale"].default_value = rayon * 0.6
    L.new(centrer.outputs[0], amp.inputs[0])
    setp = N.new("GeometryNodeSetPosition"); L.new(dist.outputs["Points"], setp.inputs["Geometry"])
    L.new(amp.outputs[0], setp.inputs["Offset"])
    ico = N.new("GeometryNodeMeshIcoSphere"); ico.inputs["Radius"].default_value = taille; ico.inputs["Subdivisions"].default_value = 1
    alea = N.new("FunctionNodeRandomValue"); alea.data_type = "FLOAT"
    alea.inputs[2].default_value = 0.4; alea.inputs[3].default_value = 1.6
    inst = N.new("GeometryNodeInstanceOnPoints")
    L.new(setp.outputs[0], inst.inputs["Points"]); L.new(ico.outputs["Mesh"], inst.inputs["Instance"])
    L.new(alea.outputs[1], inst.inputs["Scale"])
    smat = N.new("GeometryNodeSetMaterial")
    if materiau:
        smat.inputs["Material"].default_value = materiau
    L.new(inst.outputs["Instances"], smat.inputs["Geometry"])
    L.new(smat.outputs[0], sor.inputs[0])
    _modif(porteur, ng)
    porteur.visible_shadow = False
    return porteur


def anneau_scan(nom, rayon=0.6, epaisseur=0.006, hauteur=0.0, tours_par_s=0.06, materiau=None):
    bpy.ops.mesh.primitive_plane_add(size=0.01, location=(0, 0, hauteur))
    porteur = bpy.context.object; porteur.name = nom
    ng, ent, sor = _arbre(f"GN_{nom}")
    N, L = ng.nodes, ng.links
    cercle = N.new("GeometryNodeCurvePrimitiveCircle"); cercle.inputs["Resolution"].default_value = 128
    cercle.inputs["Radius"].default_value = rayon
    profil = N.new("GeometryNodeCurvePrimitiveCircle"); profil.inputs["Resolution"].default_value = 8
    profil.inputs["Radius"].default_value = epaisseur
    tube = N.new("GeometryNodeCurveToMesh")
    L.new(cercle.outputs["Curve"], tube.inputs["Curve"]); L.new(profil.outputs["Curve"], tube.inputs["Profile Curve"])
    temps = N.new("GeometryNodeInputSceneTime")
    ang = N.new("ShaderNodeMath"); ang.operation = "MULTIPLY"; ang.inputs[1].default_value = tours_par_s * 6.2832
    L.new(temps.outputs["Seconds"], ang.inputs[0])
    rot = N.new("ShaderNodeCombineXYZ"); L.new(ang.outputs[0], rot.inputs["Z"])
    tr = N.new("GeometryNodeTransform"); L.new(tube.outputs["Mesh"], tr.inputs["Geometry"]); L.new(rot.outputs[0], tr.inputs["Rotation"])
    smat = N.new("GeometryNodeSetMaterial")
    if materiau:
        smat.inputs["Material"].default_value = materiau
    L.new(tr.outputs[0], smat.inputs["Geometry"]); L.new(smat.outputs[0], sor.inputs[0])
    _modif(porteur, ng)
    return porteur


def aretes_lumineuses(obj, epaisseur=0.006, materiau=None):
    """Ajoute à l'objet des tubes lumineux le long de ses arêtes (garde la surface d'origine)."""
    ng, ent, sor = _arbre(f"GN_aretes_{obj.name}")
    N, L = ng.nodes, ng.links
    m2c = N.new("GeometryNodeMeshToCurve"); L.new(ent.outputs[0], m2c.inputs["Mesh"])
    profil = N.new("GeometryNodeCurvePrimitiveCircle"); profil.inputs["Resolution"].default_value = 4
    profil.inputs["Radius"].default_value = epaisseur
    tube = N.new("GeometryNodeCurveToMesh")
    L.new(m2c.outputs["Curve"], tube.inputs["Curve"]); L.new(profil.outputs["Curve"], tube.inputs["Profile Curve"])
    smat = N.new("GeometryNodeSetMaterial")
    if materiau:
        smat.inputs["Material"].default_value = materiau
    L.new(tube.outputs["Mesh"], smat.inputs["Geometry"])
    join = N.new("GeometryNodeJoinGeometry")
    L.new(ent.outputs[0], join.inputs[0]); L.new(smat.outputs[0], join.inputs[0])
    L.new(join.outputs[0], sor.inputs[0])
    _modif(obj, ng)
    return obj
