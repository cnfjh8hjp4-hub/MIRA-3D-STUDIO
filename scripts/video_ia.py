"""Modèles vidéo IA ouverts (famille de Kling) sur leurs démos Hugging Face, avec le jeton HF_TOKEN du propriétaire.
Aucun paiement : le calcul gratuit du compte Hugging Face est utilisé.
  python3 scripts/video_ia.py api                                  liste l'API des Spaces candidats
  python3 scripts/video_ia.py s2v IMAGE VOIX SORTIE.mp4 [480P|720P]  image + voix → vidéo qui parle (Wan 2.2 S2V)
  python3 scripts/video_ia.py i2v IMAGE "PROMPT" SORTIE.mp4 [secondes]  image + prompt → vidéo (Wan 2.2 image vers vidéo)"""
import os
import shutil
import sys
import time

from gradio_client import Client, handle_file

TOK = os.environ.get("HF_TOKEN") or None
SPACES = {"s2v": ["Wan-AI/Wan2.2-S2V"], "i2v": ["zerogpu-aoti/wan2-2-fp8da-aoti-faster", "multimodalart/wan2-1-fast"]}
NEG = ("morphing, extra eyes, extra beak, human mouth, teeth, distorted face, melting, flicker, text, watermark, "
       "fast camera, blurry, low quality")


def client(nom):
    try:
        return Client(nom, token=TOK) if TOK else Client(nom)
    except TypeError:
        return Client(nom, hf_token=TOK) if TOK else Client(nom)


def video(res, sortie):
    pile = [res]
    while pile:
        x = pile.pop()
        if isinstance(x, (list, tuple)):
            pile.extend(x)
        elif isinstance(x, dict):
            pile.extend(x.values())
        elif isinstance(x, str) and x.lower().endswith((".mp4", ".webm")) and os.path.exists(x):
            os.makedirs(os.path.dirname(os.path.abspath(sortie)), exist_ok=True); shutil.copy(x, sortie); return sortie
    raise RuntimeError("pas de vidéo dans la réponse : " + repr(res)[:400])


def main():
    mode = sys.argv[1]; t = time.time()
    print("jeton Hugging Face :", "présent" if TOK else "ABSENT (quota quasi nul)", flush=True)
    if mode == "api":
        for k, lst in SPACES.items():
            for s in lst:
                try:
                    print(f"===== {s}\n" + client(s).view_api(return_format="str", print_info=False)[:3000])
                except Exception as e:
                    print(f"===== {s} indisponible : {e!r}"[:300])
        return
    if mode == "s2v":
        img, voix, sortie = sys.argv[2:5]; res_ = sys.argv[5] if len(sys.argv) > 5 else "480P"
        c = client(SPACES["s2v"][0])
        r = c.predict(ref_img=handle_file(img), audio=handle_file(voix), resolution=res_, api_name="/predict")
    else:
        img, prompt, sortie = sys.argv[2:5]; d = float(sys.argv[5]) if len(sys.argv) > 5 else 5.0
        derniere = None
        for s in SPACES["i2v"]:
            try:
                c = client(s)
                if "aoti" in s:
                    r = c.predict(input_image=handle_file(img), prompt=prompt, steps=6, negative_prompt=NEG, duration_seconds=d,
                                  guidance_scale=1, guidance_scale_2=1, seed=42, randomize_seed=False, api_name="/generate_video")
                else:
                    r = c.predict(input_image=handle_file(img), prompt=prompt, height=832, width=480, negative_prompt=NEG,
                                  duration_seconds=d, guidance_scale=1, steps=4, seed=42, randomize_seed=False, api_name="/generate_video")
                break
            except Exception as e:
                derniere = e; print(s, "échec :", repr(e)[:300], flush=True)
        else:
            raise derniere
    print("vidéo :", video(r, sortie), f"({time.time() - t:.0f} s)", flush=True)


if __name__ == "__main__":
    main()
