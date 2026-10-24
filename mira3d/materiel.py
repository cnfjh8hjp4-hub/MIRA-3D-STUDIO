"""Détection du matériel (CPU, RAM, GPU, mémoire vidéo) et des moteurs Blender qui fonctionnent VRAIMENT ici.
Le résultat est mis en cache (cache/materiel.json) : la sonde ne tourne qu'une fois par machine et version de Blender."""
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile

from .commun import CACHE, RACINE, blender_bin, ecrire_json, lancer

FICHIER = os.path.join(CACHE, "materiel.json")


def _cpu():
    modele = ""
    try:
        modele = next(l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
    except Exception:
        modele = platform.processor()
    return {"coeurs": os.cpu_count(), "modele": modele}


def _ram_go():
    try:
        kb = int(re.search(r"MemTotal:\s+(\d+)", open("/proc/meminfo").read()).group(1))
        return round(kb / 1024 / 1024, 1)
    except Exception:
        return None


def _gpus():
    out = []
    if shutil.which("nvidia-smi"):
        try:
            txt = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                                 capture_output=True, text=True, timeout=20).stdout
            for l in txt.strip().splitlines():
                n, m = [x.strip() for x in l.split(",")]
                out.append({"nom": n, "memoire_video_go": round(int(m) / 1024, 1), "marque": "NVIDIA"})
        except Exception:
            pass
    return out


def _version_blender(b):
    try:
        return subprocess.run([b, "--version"], capture_output=True, text=True, timeout=60).stdout.splitlines()[0]
    except Exception:
        return None


def _sonde(b, moteur, appareil, prefixe, journal):
    d = tempfile.mkdtemp(prefix="sonde_")
    cmd = prefixe + [b, "-b", "--factory-startup", "-P", os.path.join(RACINE, "bibliotheque", "sonde.py"), "--",
                     "--moteur", moteur, "--appareil", appareil, "--sortie", d]
    code, sec = lancer(cmd, journal, timeout=240)
    txt = open(journal).read()
    m = re.findall(r"MIRA3D_SONDE (\{.*\})", txt)
    res = json.loads(m[-1]) if m else {"ok": False, "erreur": f"pas de réponse (code {code})"}
    res["code"] = code; res["prefixe"] = prefixe
    return res


def detecter(rafraichir=False):
    b = blender_bin()
    base = {"cpu": _cpu(), "ram_go": _ram_go(), "gpu": _gpus(), "machine": platform.node(),
            "blender": {"chemin": b, "version": _version_blender(b) if b else None}}
    cle = f"{base['machine']}|{base['blender']['version']}|{base['cpu']['coeurs']}|{len(base['gpu'])}"
    if not rafraichir and os.path.exists(FICHIER):
        try:
            c = json.load(open(FICHIER))
            if c.get("cle") == cle:
                return c
        except Exception:
            pass
    moteurs = {}
    if b:
        os.makedirs(CACHE, exist_ok=True)
        journal = os.path.join(CACHE, "sonde.log")
        open(journal, "w").close()
        cy = _sonde(b, "cycles", "CPU", [], journal)
        moteurs["cycles"] = cy
        if cy.get("gpu"):
            moteurs["cycles_gpu"] = _sonde(b, "cycles", "GPU", [], journal)
        ee = _sonde(b, "eevee", "CPU", [], journal)
        if not ee.get("ok") and shutil.which("xvfb-run"):  # EEVEE a besoin d'OpenGL : écran virtuel logiciel
            ee2 = _sonde(b, "eevee", "CPU", ["xvfb-run", "-a", "-s", "-screen 0 1280x1024x24"], journal)
            ee2["essai_direct"] = ee.get("erreur") or f"code {ee.get('code')}"
            ee = ee2
        moteurs["eevee"] = ee
    base["moteurs"] = {k: {kk: v.get(kk) for kk in ("ok", "secondes", "erreur", "prefixe", "gpu", "essai_direct", "code") if kk in v}
                       for k, v in moteurs.items()}
    base["moteurs_ok"] = [k for k, v in moteurs.items() if v.get("ok")]
    base["cle"] = cle
    ecrire_json(FICHIER, base)
    return base


def resume(m):
    g = ", ".join(f"{x['nom']} ({x['memoire_video_go']} Go)" for x in m["gpu"]) or "aucun"
    lignes = [f"CPU      : {m['cpu']['coeurs']} cœurs, {m['cpu']['modele']}", f"RAM      : {m['ram_go']} Go", f"GPU      : {g}",
              f"Blender  : {m['blender']['version']}"]
    for k, v in m.get("moteurs", {}).items():
        etat = f"OK ({v.get('secondes')} s pour l'image test)" if v.get("ok") else f"indisponible : {v.get('erreur') or v.get('code')}"
        if v.get("ok") and v.get("prefixe"):
            etat += " via écran virtuel (xvfb)"
        lignes.append(f"{k:9}: {etat}")
    return "\n".join(lignes)
