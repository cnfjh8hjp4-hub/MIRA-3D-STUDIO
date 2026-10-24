"""Exécution standard d'une scène, côté Blender. Une scène appelle :

    from bibliotheque import execution
    execution.lancer(construire, {"nom": "demo", "duree_s": 5, "fps": 24, "personnages": ["mira"], "audio": None})

Modes (choisis par le Render Manager / le Quality Inspector, arguments après « -- ») :
  --mode inspection   décrit la scène (caméra, timeline, ressources manquantes, cadrage) → inspection.json
  --mode images       rend quelques images tests (--frames 1,60,120) → test_0001.png… + temps
  --mode frames       rend une plage (--frames 1-120) en PNG, SANS écraser les images existantes (reprise)
Le profil de rendu arrive en JSON (--profil-json)."""
import argparse
import json
import math
import os
import sys
import time

import bpy


def _args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="images", choices=["inspection", "images", "frames"])
    ap.add_argument("--profil-json", default="")
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--frames", default="")
    a, _ = ap.parse_known_args(argv)
    return a


def moteurs_disponibles():
    return [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]


def nom_moteur(m):
    dispo = moteurs_disponibles()
    if m == "eevee":
        for n in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
            if n in dispo:
                return n
    if m == "cycles":
        return "CYCLES"
    return m


def _essai(fn):
    try:
        fn()
    except Exception as e:  # réglage absent de cette version de Blender : on continue
        print("réglage ignoré :", e)


def appliquer_profil(p):
    sc = bpy.context.scene; r = sc.render
    r.engine = nom_moteur(p["moteur"])
    r.resolution_x, r.resolution_y = p["largeur"], p["hauteur"]; r.resolution_percentage = 100
    r.use_persistent_data = True  # garde les données entre les images d'une animation : plus rapide
    r.film_transparent = False
    if p["moteur"] == "cycles":
        cy = sc.cycles
        cy.device = "GPU" if p.get("appareil") == "GPU" else "CPU"
        if cy.device == "GPU":
            pr = bpy.context.preferences.addons["cycles"].preferences
            pr.compute_device_type = p.get("api_gpu", "OPTIX"); pr.get_devices()
            for d in pr.devices:
                d.use = d.type != "CPU"
        cy.samples = p["echantillons"]; cy.use_adaptive_sampling = True
        cy.adaptive_threshold = p.get("seuil_adaptatif", 0.02)
        cy.use_denoising = p.get("debruitage", True)
        _essai(lambda: setattr(cy, "denoiser", "OPENIMAGEDENOISE"))
        cy.max_bounces = p.get("rebonds", 4); cy.diffuse_bounces = min(2, cy.max_bounces)
        cy.glossy_bounces = p.get("rebonds_reflets", 2); cy.transmission_bounces = p.get("rebonds", 4)
        cy.transparent_max_bounces = p.get("rebonds_transparence", 12)
        cy.caustics_reflective = False; cy.caustics_refractive = False
        cy.sample_clamp_indirect = p.get("clamp_indirect", 8.0)
        _essai(lambda: setattr(cy, "use_light_tree", True))
    else:
        ee = sc.eevee
        ee.taa_render_samples = p["echantillons"]
        _essai(lambda: setattr(ee, "use_raytracing", p.get("lancer_rayons", True)))
        _essai(lambda: setattr(ee, "ray_tracing_method", "SCREEN"))
        _essai(lambda: setattr(ee, "use_shadows", True))
        _essai(lambda: setattr(ee, "shadow_ray_count", 2))
        _essai(lambda: setattr(ee, "use_volumetric_shadows", False))
    vs = sc.view_settings
    _essai(lambda: setattr(vs, "view_transform", p.get("transformation", "Standard")))
    if p.get("look"):
        _essai(lambda: setattr(vs, "look", p["look"]))
    if p.get("flou_mouvement"):
        r.use_motion_blur = True
    # lueur (glow) commune aux deux moteurs, au compositing
    sc.use_nodes = True; nt = sc.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    rl = nt.nodes.new("CompositorNodeRLayers"); comp = nt.nodes.new("CompositorNodeComposite")
    dernier = rl.outputs["Image"]
    if p.get("glow", True):
        g = nt.nodes.new("CompositorNodeGlare"); g.glare_type = "FOG_GLOW"; g.threshold = p.get("seuil_glow", 0.8)
        g.size = p.get("taille_glow", 7); g.mix = 0.0
        _essai(lambda: setattr(g, "quality", p.get("qualite_glow", "MEDIUM")))
        nt.links.new(dernier, g.inputs["Image"]); dernier = g.outputs["Image"]
    nt.links.new(dernier, comp.inputs["Image"])


def _frames(spec, sc):
    if not spec:
        return list(range(sc.frame_start, sc.frame_end + 1))
    if "-" in spec:
        a, b = spec.split("-"); return list(range(int(a), int(b) + 1))
    return [int(x) for x in spec.split(",") if x.strip()]


def inspection(meta, sortie):
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    sc = bpy.context.scene; cam = sc.camera
    manquantes = []
    for im in bpy.data.images:
        if im.source == "FILE" and not im.packed_file:
            f = bpy.path.abspath(im.filepath)
            if f and not os.path.exists(f):
                manquantes.append({"type": "texture", "nom": im.name, "chemin": f})
    for lib in bpy.data.libraries:
        f = bpy.path.abspath(lib.filepath)
        if not os.path.exists(f):
            manquantes.append({"type": "bibliotheque", "nom": lib.name, "chemin": f})
    audio = []
    if sc.sequence_editor:
        for s in sc.sequence_editor.sequences_all:
            if s.type == "SOUND":
                f = bpy.path.abspath(s.sound.filepath); audio.append(f)
                if not os.path.exists(f):
                    manquantes.append({"type": "audio", "nom": s.name, "chemin": f})
    cadrage = []
    if cam:
        meshes = [o for o in sc.objects if o.type == "MESH" and not o.hide_render and not o.name.startswith(("sol", "bokeh"))]
        for f in sorted({sc.frame_start, (sc.frame_start + sc.frame_end) // 2, sc.frame_end}):
            sc.frame_set(f)
            vus = 0
            for o in meshes:
                c = o.matrix_world @ (sum((Vector(b) for b in o.bound_box), Vector()) / 8)
                v = world_to_camera_view(sc, cam, c)
                if 0 <= v.x <= 1 and 0 <= v.y <= 1 and v.z > 0:
                    vus += 1
            cadrage.append({"image": f, "objets_dans_le_champ": vus, "objets": len(meshes)})
    info = {
        "blender": bpy.app.version_string, "moteurs_disponibles": moteurs_disponibles(),
        "meta": meta, "camera": cam.name if cam else None,
        "resolution": [sc.render.resolution_x, sc.render.resolution_y], "fps": sc.render.fps,
        "timeline": [sc.frame_start, sc.frame_end], "duree_s": round((sc.frame_end - sc.frame_start + 1) / sc.render.fps, 3),
        "objets": {t: sum(1 for o in sc.objects if o.type == t) for t in {o.type for o in sc.objects}},
        "materiaux": len(bpy.data.materials), "geometry_nodes": sum(1 for g in bpy.data.node_groups if g.bl_idname == "GeometryNodeTree"),
        "ressources_manquantes": manquantes, "audio": audio, "cadrage": cadrage, "moteur": sc.render.engine,
    }
    json.dump(info, open(os.path.join(sortie, "inspection.json"), "w"), indent=2, ensure_ascii=False)
    print("MIRA3D_INSPECTION_OK", flush=True)


def _journal_temps(chemin):
    debut = {}

    def pre(sc, *_):
        debut["t"] = time.time()

    def post(sc, *_):
        with open(chemin, "a") as f:
            f.write(json.dumps({"image": sc.frame_current, "secondes": round(time.time() - debut.get("t", time.time()), 3)}) + "\n")
    bpy.app.handlers.render_pre.append(pre); bpy.app.handlers.render_post.append(post)


def lancer(construire, meta):
    a = _args()
    os.makedirs(a.sortie, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    fps = meta.get("fps", 24)
    sc.render.fps = fps; sc.frame_start = 1; sc.frame_end = int(round(meta["duree_s"] * fps))
    construire(meta)
    if a.profil_json:
        appliquer_profil(json.load(open(a.profil_json)))
    if meta.get("audio") and os.path.exists(meta["audio"]):
        sc.sequence_editor_create(); sc.sequence_editor.sequences.new_sound("voix", meta["audio"], 1, 1)
    if a.mode == "inspection":
        return inspection(meta, a.sortie)
    _journal_temps(os.path.join(a.sortie, "temps_images.jsonl"))
    r = sc.render; r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"
    if a.mode == "images":
        for f in _frames(a.frames, sc):
            sc.frame_set(f); r.filepath = os.path.join(a.sortie, f"test_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
    else:
        fr = _frames(a.frames, sc); sc.frame_start, sc.frame_end = fr[0], fr[-1]
        r.use_overwrite = False; r.use_placeholder = True  # reprise : les images déjà rendues ne sont pas refaites
        r.filepath = os.path.join(a.sortie, "####")
        bpy.ops.render.render(animation=True)
    print("MIRA3D_RENDU_OK", flush=True)
