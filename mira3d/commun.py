import json
import os
import shutil
import subprocess
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(RACINE, "cache")
RAPPORTS = os.path.join(RACINE, "rapports")


def blender_bin():
    b = os.environ.get("BLENDER_BIN")
    return b if b and os.path.exists(b) else shutil.which("blender")


def lancer(cmd, journal, timeout=None, env=None):
    """Lance une commande, journal complet dans un fichier. Renvoie (code, secondes)."""
    t = time.time()
    with open(journal, "a") as f:
        f.write(f"\n$ {' '.join(cmd)}\n"); f.flush()
        try:
            code = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=timeout,
                                  env={**os.environ, **(env or {})}).returncode
        except subprocess.TimeoutExpired:
            f.write(f"\n[délai dépassé : {timeout} s]\n"); code = -9
    return code, round(time.time() - t, 2)


def ecrire_json(chemin, data):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def horodatage():
    return time.strftime("%Y%m%d-%H%M%S")
