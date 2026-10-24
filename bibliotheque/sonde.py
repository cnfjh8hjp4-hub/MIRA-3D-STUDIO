"""Sonde : ce moteur de rendu fonctionne-t-il VRAIMENT ici ? Rend une image 64x64 et mesure le temps.
Usage : blender -b --factory-startup -P bibliotheque/sonde.py -- --moteur cycles|eevee [--appareil CPU|GPU] --sortie D"""
import argparse, json, os, sys, time
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser(); ap.add_argument("--moteur"); ap.add_argument("--appareil", default="CPU"); ap.add_argument("--sortie")
a = ap.parse_args(argv)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bibliotheque.execution import nom_moteur, moteurs_disponibles  # noqa: E402

res = {"moteur": a.moteur, "appareil": a.appareil, "ok": False, "blender": bpy.app.version_string, "gpu": []}
try:
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.mesh.primitive_monkey_add(); bpy.ops.object.light_add(type="SUN")
    bpy.ops.object.camera_add(location=(0, -4, 0), rotation=(1.5708, 0, 0)); sc.camera = bpy.context.object
    sc.render.engine = nom_moteur(a.moteur); sc.render.resolution_x = sc.render.resolution_y = 64
    if a.moteur == "cycles":
        pr = bpy.context.preferences.addons["cycles"].preferences
        for api in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
            try:
                pr.compute_device_type = api; pr.get_devices()
                res["gpu"] += [{"api": api, "nom": d.name} for d in pr.devices if d.type != "CPU"]
            except Exception:
                pass
        if a.appareil == "GPU":
            if not res["gpu"]:
                raise RuntimeError("aucun GPU utilisable par Cycles")
            pr.compute_device_type = res["gpu"][0]["api"]; pr.get_devices()
            for d in pr.devices:
                d.use = d.type != "CPU"
            sc.cycles.device = "GPU"
        sc.cycles.samples = 4
    else:
        sc.eevee.taa_render_samples = 4
    sc.render.filepath = os.path.join(a.sortie, f"sonde_{a.moteur}_{a.appareil}.png")
    t = time.time(); bpy.ops.render.render(write_still=True); res["secondes"] = round(time.time() - t, 2)
    res["ok"] = os.path.exists(sc.render.filepath)
except Exception as e:
    res["erreur"] = str(e)[:300]
print("MIRA3D_SONDE " + json.dumps(res), flush=True)
