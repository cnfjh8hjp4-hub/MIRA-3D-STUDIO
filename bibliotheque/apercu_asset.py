"""Teste l'import d'une ressource dans Blender et rend son aperçu (256x256).
Usage : blender -b --factory-startup -P bibliotheque/apercu_asset.py -- --fichier F --type T --png P --json J"""
import argparse, json, math, os, sys, time, traceback
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser()
for k in ("--fichier", "--type", "--png", "--json"):
    ap.add_argument(k)
a = ap.parse_args(argv)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bibliotheque import import_assets  # noqa: E402

res = {"fichier": a.fichier, "type": a.type, "ok": False, "blender": bpy.app.version_string}
t0 = time.time()
try:
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    w = bpy.data.worlds.new("w"); w.use_nodes = True; sc.world = w
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.02, 0.03, 0.05, 1)
    cible = (0, 0, 0.5); dist = 2.6
    if a.type == "hdri":
        env = w.node_tree.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(a.fichier)
        w.node_tree.links.new(env.outputs[0], bg.inputs[0])
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 0.5)); s = bpy.context.object; bpy.ops.object.shade_smooth()
        m = bpy.data.materials.new("chrome"); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Metallic"].default_value = 1; p.inputs["Roughness"].default_value = 0.05; s.data.materials.append(m)
        res["stats"] = {"resolution": list(env.image.size)}
    elif a.type == "materiau":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 0.5)); s = bpy.context.object; bpy.ops.object.shade_smooth()
        m = bpy.data.materials.new("pbr"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        d = os.path.dirname(a.fichier)
        for f in sorted(os.listdir(d)):
            fl = f.lower(); fp = os.path.join(d, f)
            if not fl.endswith((".jpg", ".png")):
                continue
            if any(k in fl for k in ("diff", "color", "albedo")):
                t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(fp); L.new(t.outputs[0], p.inputs["Base Color"])
            elif "rough" in fl:
                t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(fp); t.image.colorspace_settings.name = "Non-Color"
                L.new(t.outputs[0], p.inputs["Roughness"])
            elif "nor" in fl and "gl" in fl:
                t = N.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(fp); t.image.colorspace_settings.name = "Non-Color"
                nm = N.new("ShaderNodeNormalMap"); L.new(t.outputs[0], nm.inputs["Color"]); L.new(nm.outputs[0], p.inputs["Normal"])
        s.data.materials.append(m); res["stats"] = {"textures": len(bpy.data.images)}
    elif a.type == "mouvement":
        objs = import_assets.importer(a.fichier)
        arm = next(o for o in objs if o.type == "ARMATURE")
        act = arm.animation_data.action
        res["stats"] = {"os": len(arm.data.bones), "noms_os": [b.name for b in arm.data.bones][:40],
                        "images": int(act.frame_range[1] - act.frame_range[0] + 1)}
        import mathutils
        pts = [arm.matrix_world @ b.head_local for b in arm.data.bones]
        hz = max(p.z for p in pts) - min(p.z for p in pts); k = 1.7 / max(hz, 1e-6)
        arm.scale = (k, k, k); bpy.context.view_layer.update()
        sc.frame_set(int(act.frame_range[0] + (act.frame_range[1] - act.frame_range[0]) / 2))
        arm.data.display_type = "STICK"
        # rendu des os en bâtonnets : convertit en maillage via des cylindres
        m = bpy.data.materials.new("os"); m.use_nodes = True
        N = m.node_tree.nodes; N.clear(); e = N.new("ShaderNodeEmission"); e.inputs[0].default_value = (0.17, 0.9, 1, 1); e.inputs[1].default_value = 4
        o_ = N.new("ShaderNodeOutputMaterial"); m.node_tree.links.new(e.outputs[0], o_.inputs[0])
        bpy.context.view_layer.update()
        for pb in arm.pose.bones:
            h = arm.matrix_world @ pb.head; t = arm.matrix_world @ pb.tail; v = t - h
            if v.length < 1e-4:
                continue
            bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=v.length, location=(h + t) / 2)
            c = bpy.context.object; c.rotation_mode = "QUATERNION"; c.rotation_quaternion = mathutils.Vector((0, 0, 1)).rotation_difference(v)
            c.data.materials.append(m)
        objs = [o for o in sc.objects if o.type == "MESH"]
        mn, mx = import_assets.boite(objs); cible = tuple((mn + mx) / 2); dist = max(mx - mn) * 1.6
    else:
        objs = import_assets.importer(a.fichier)
        res["stats"] = import_assets.statistiques(objs)
        mn, mx = import_assets.boite(objs)
        if res["stats"]["maillages"] == 0:
            raise RuntimeError("aucun maillage importé")
        cible = tuple((mn + mx) / 2); dist = max(mx - mn) * 1.8 + 1e-3
        res["stats"]["dimensions_m"] = [round(x, 3) for x in (mx - mn)]
    bpy.ops.object.light_add(type="AREA", location=(cible[0] - dist, cible[1] - dist, cible[2] + dist)); l = bpy.context.object
    l.data.energy = 300 * dist * dist; l.data.size = dist
    tc = l.constraints.new("TRACK_TO"); e_ = bpy.data.objects.new("c", None); e_.location = cible; sc.collection.objects.link(e_); tc.target = e_
    bpy.ops.object.camera_add(location=(cible[0] + dist * math.sin(0.6), cible[1] - dist * math.cos(0.6), cible[2] + dist * 0.45))
    cam = bpy.context.object; sc.camera = cam; t = cam.constraints.new("TRACK_TO"); t.target = e_
    sc.render.engine = "CYCLES"; sc.cycles.samples = 16; sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = 256; sc.render.filepath = a.png
    bpy.ops.render.render(write_still=True)
    res["ok"] = os.path.exists(a.png)
except Exception as e:
    res["erreur"] = f"{type(e).__name__}: {e}"[:400]; res["trace"] = traceback.format_exc()[-800:]
res["secondes"] = round(time.time() - t0, 2)
json.dump(res, open(a.json, "w"), indent=2, ensure_ascii=False)
print("MIRA3D_APERCU", json.dumps({k: res.get(k) for k in ("ok", "erreur", "secondes")}), flush=True)
