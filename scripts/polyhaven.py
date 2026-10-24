"""Télécharge une ressource CC0 de Poly Haven (HDRI, texture, modèle) dans cache/polyhaven/, une seule fois.
Usage : python3 scripts/polyhaven.py hdris|textures|models IDENTIFIANT [1k|2k|4k]
Licence : CC0 (domaine public), crédit facultatif mais apprécié : https://polyhaven.com/a/IDENTIFIANT
Chaque téléchargement est noté dans cache/polyhaven/LICENCES.md."""
import json
import os
import sys
import time
import urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(RACINE, "cache", "polyhaven")
API = "https://api.polyhaven.com"
UA = {"User-Agent": "MIRA-3D-STUDIO (usage CC0 respectueux)"}


def _json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def telecharger(type_, ident, res="1k"):
    dossier = os.path.join(CACHE, type_); os.makedirs(dossier, exist_ok=True)
    deja = [f for f in os.listdir(dossier) if f.startswith(f"{ident}_{res}")]
    if deja:
        print("déjà en cache :", deja[0]); return os.path.join(dossier, deja[0])
    info = _json(f"{API}/info/{ident}")
    fichiers = _json(f"{API}/files/{ident}")
    if type_ == "hdris":
        choix = fichiers["hdri"][res].get("hdr") or fichiers["hdri"][res]["exr"]; ext = choix["url"].rsplit(".", 1)[-1]
        cibles = [(choix["url"], os.path.join(dossier, f"{ident}_{res}.{ext}"))]
    elif type_ == "textures":
        cibles = []
        for carte in ("Diffuse", "nor_gl", "Rough", "AO", "Displacement"):
            if carte in fichiers and res in fichiers[carte]:
                c = fichiers[carte][res].get("jpg") or fichiers[carte][res].get("png")
                cibles.append((c["url"], os.path.join(dossier, f"{ident}_{res}_{carte}.{c['url'].rsplit('.', 1)[-1]}")))
    else:
        c = fichiers["gltf"][res]["gltf"]; cibles = [(c["url"], os.path.join(dossier, f"{ident}_{res}.gltf"))]
        for chemin, inc in c.get("include", {}).items():
            cibles.append((inc["url"], os.path.join(dossier, f"{ident}_{res}", chemin)))
    for url, dest in cibles:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(dest, "wb") as f:
            f.write(r.read())
        print("téléchargé :", os.path.relpath(dest, RACINE))
    with open(os.path.join(CACHE, "LICENCES.md"), "a") as f:
        f.write(f"- {time.strftime('%Y-%m-%d')} · {type_} « {info.get('name', ident)} » ({res}) · CC0 · auteurs : "
                f"{', '.join(info.get('authors', {}).keys())} · https://polyhaven.com/a/{ident}\n")
    return cibles[0][1]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    telecharger(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "1k")
