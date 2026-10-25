"""Génère un modèle 3D (.glb texturé) à partir d'une image officielle d'un personnage, avec TRELLIS (licence MIT)
sur sa démo gratuite Hugging Face. Hunyuan3D n'est PAS utilisé : sa licence exclut l'Union européenne.
Usage : python3 scripts/generer_3d.py IMAGE SORTIE.glb [graine]"""
import os
import shutil
import sys
import time

from gradio_client import Client, handle_file

img, sortie = sys.argv[1], sys.argv[2]
graine = int(sys.argv[3]) if len(sys.argv) > 3 else 0
tok = os.environ.get("HF_TOKEN") or None
t = time.time()
for space in ("trellis-community/TRELLIS", "JeffreyXiang/TRELLIS"):
    try:
        c = Client(space, token=tok) if tok else Client(space)
    except Exception as e:
        print(space, "indisponible :", repr(e)[:200]); continue
    try:
        c.predict(api_name="/start_session")
    except Exception:
        pass
    pre = c.predict(handle_file(img), api_name="/preprocess_image")
    res = c.predict(image=handle_file(pre), multiimages=[], seed=graine, ss_guidance_strength=7.5, ss_sampling_steps=12,
                    slat_guidance_strength=3, slat_sampling_steps=12, multiimage_algo="stochastic",
                    mesh_simplify=0.92, texture_size=1024, api_name="/generate_and_extract_glb")
    pile = [res]
    while pile:
        x = pile.pop()
        if isinstance(x, (list, tuple)):
            pile.extend(x)
        elif isinstance(x, dict):
            pile.extend(x.values())
        elif isinstance(x, str) and x.lower().endswith(".glb") and os.path.exists(x):
            os.makedirs(os.path.dirname(os.path.abspath(sortie)), exist_ok=True); shutil.copy(x, sortie)
            print(f"modèle : {sortie} ({os.path.getsize(sortie) // 1024} Ko, {time.time() - t:.0f} s, {space})"); sys.exit(0)
    print("pas de .glb dans la réponse :", repr(res)[:500])
sys.exit(1)
