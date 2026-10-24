"""Importateur Blender des ressources de la bibliothèque + adaptation des matériaux au style Mira.
Formats : .glb/.gltf, .fbx, .obj, .bvh (mouvement), .blend (ajout des objets), .hdr/.exr (fond), .jpg/.png (matériau)."""
import os

import bpy
from mathutils import Vector

from . import geonodes, materiaux
from .palettes import PALETTES


def importer(chemin):
    """Importe un fichier et renvoie les nouveaux objets."""
    avant = set(bpy.data.objects)
    ext = os.path.splitext(chemin)[1].lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=chemin)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=chemin)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=chemin)
    elif ext == ".bvh":
        bpy.ops.import_anim.bvh(filepath=chemin, use_fps_scale=True, update_scene_fps=False, update_scene_duration=False)
    elif ext == ".blend":
        with bpy.data.libraries.load(chemin, link=False) as (src, dst):
            dst.objects = src.objects
        for o in dst.objects:
            if o:
                bpy.context.scene.collection.objects.link(o)
    else:
        raise ValueError(f"format non pris en charge : {ext}")
    return [o for o in bpy.data.objects if o not in avant]


def boite(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    if not pts:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def regrouper(objs, nom, hauteur=None, position=(0, 0, 0), rotation_z=0.0):
    """Met les objets sous un pivot, à la hauteur voulue (mètres), posés au sol à la position donnée."""
    import math
    pivot = bpy.data.objects.new(nom, None); bpy.context.scene.collection.objects.link(pivot)
    for o in objs:
        if o.parent is None:
            o.parent = pivot
    bpy.context.view_layer.update()
    mn, mx = boite(objs)
    k = (hauteur / max(1e-6, mx.z - mn.z)) if hauteur else 1.0
    pivot.scale = (k, k, k)
    c = (mn + mx) / 2
    pivot.location = (position[0] - c.x * k, position[1] - c.y * k, position[2] - mn.z * k)
    pivot.rotation_euler = (0, 0, math.radians(rotation_z))
    bpy.context.view_layer.update()
    return pivot


def adapter_materiaux(objs, style="sombre_aretes", palette="mira", epaisseur=0.004):
    """sombre_aretes : surfaces noires brillantes + arêtes lumineuses (Geometry Nodes) dans la couleur du personnage.
    hologramme : matériau holographique de la palette. garder : matériaux d'origine."""
    if style == "garder":
        return
    pal = PALETTES[palette]
    noir = materiaux.sol_brillant(f"objet_noir_{palette}", "#070b14", 0.3)
    arete = materiaux.emission(f"arete_{palette}", pal["principal"], 3.5)
    holo = materiaux.hologramme(f"holo_objet_{palette}", pal["principal"], pal["lumiere"], force=1.2, opacite=0.6)
    for o in objs:
        if o.type != "MESH":
            continue
        o.data.materials.clear()
        o.data.materials.append(holo if style == "hologramme" else noir)
        if style == "sombre_aretes" and len(o.data.edges) < 20000:
            geonodes.aretes_lumineuses(o, epaisseur, arete)


def statistiques(objs):
    meshes = [o for o in objs if o.type == "MESH"]
    return {"objets": len(objs), "maillages": len(meshes), "polygones": sum(len(o.data.polygons) for o in meshes),
            "materiaux": sorted({m.name for o in meshes for m in o.data.materials if m}),
            "armatures": sum(1 for o in objs if o.type == "ARMATURE")}
