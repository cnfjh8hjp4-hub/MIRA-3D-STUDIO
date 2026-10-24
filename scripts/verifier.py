"""Vérifie les versions et dépendances du studio. Écrit rapports/verification.json.
Usage : python3 scripts/verifier.py [--court]"""
import json, os, platform, shutil, subprocess, sys, time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(RACINE, "config", "rendu.json")))


def cmd(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:
        return f"ERREUR : {e}"


def blender_bin():
    return os.environ.get("BLENDER_BIN") if os.environ.get("BLENDER_BIN") and os.path.exists(os.environ["BLENDER_BIN"]) \
        else shutil.which("blender")


def verifier():
    b = blender_bin()
    bv = cmd([b, "--version"]).splitlines()[0] if b else ""
    fv = cmd(["ffmpeg", "-version"]).splitlines()[0] if shutil.which("ffmpeg") else ""
    libre = shutil.disk_usage(RACINE).free / 1e9
    try:
        import pytest  # noqa
        import numpy  # noqa
        import PIL  # noqa
        pt = pytest.__version__
    except Exception:
        pt = ""
    res = {
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": {"ok": sys.version_info >= (3, 10), "version": platform.python_version()},
        "blender": {"ok": os.environ.get("BLENDER_VERSION", CFG["blender_version"]) in bv, "version": bv or "absent", "attendu": CFG["blender_version"],
                    "chemin": b},
        "ffmpeg": {"ok": bool(fv), "version": fv or "absent"},
        "pytest": {"ok": bool(pt), "version": pt or "absent"},
        "processeurs": os.cpu_count(),
        "disque_libre_go": round(libre, 1),
        "disque_ok": libre > 3,
    }
    res["tout_ok"] = all(v["ok"] for v in res.values() if isinstance(v, dict)) and res["disque_ok"]
    return res


if __name__ == "__main__":
    r = verifier()
    os.makedirs(os.path.join(RACINE, "rapports"), exist_ok=True)
    json.dump(r, open(os.path.join(RACINE, "rapports", "verification.json"), "w"), indent=2, ensure_ascii=False)
    for k in ("python", "blender", "ffmpeg", "pytest"):
        print(f"{'OK ' if r[k]['ok'] else 'NON'} {k:8} {r[k]['version']}")
    if "--court" not in sys.argv:
        print(f"    CPU : {r['processeurs']} cœurs · disque libre : {r['disque_libre_go']} Go")
    print("Studio prêt." if r["tout_ok"] else "Il manque quelque chose : lance  bash scripts/installer.sh")
    sys.exit(0 if r["tout_ok"] else 1)
