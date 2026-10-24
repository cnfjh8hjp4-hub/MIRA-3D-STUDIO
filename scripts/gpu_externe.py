"""Interface pour un futur serveur GPU externe (SSH). Aucun serveur n'est loué : par défaut, mode « plan » seulement.
  python3 scripts/gpu_externe.py plan SCENE            montre ce qui serait fait, sans rien lancer
  python3 scripts/gpu_externe.py executer SCENE --accord   exige config/gpu_externe.json (actif=true) + secrets
"""
import json
import os
import shlex
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def config():
    f = os.path.join(RACINE, "config", "gpu_externe.json")
    return json.load(open(f)) if os.path.exists(f) else json.load(open(os.path.join(RACINE, "config", "gpu_externe.exemple.json")))


def etapes(c, scene):
    d = c["dossier_distant"]; h = "$MIRA3D_GPU_UTILISATEUR@$MIRA3D_GPU_HOTE"
    return [f"rsync -az --exclude sorties --exclude .git ./ {h}:{d}/",
            f"ssh {h} 'cd {d} && bash scripts/installer.sh && ./studio produire {shlex.quote(scene)} --profil {c['profil']} --accord'",
            f"rsync -az {h}:{d}/sorties/ ./sorties/ && rsync -az {h}:{d}/rapports/ ./rapports/"]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    action, scene = sys.argv[1], sys.argv[2]; c = config()
    print("Configuration :", "ACTIVE" if c.get("actif") else "inactive (aucun serveur)")
    for e in etapes(c, scene):
        print("  ", e)
    if action == "executer":
        manquants = [s for s in c["secrets_attendus"] if not os.environ.get(s)]
        if "--accord" not in sys.argv or not c.get("actif") or manquants:
            sys.exit("Refusé : il faut --accord, config/gpu_externe.json avec actif=true et les secrets " + ", ".join(manquants or c["secrets_attendus"]))
        for e in etapes(c, scene):
            if subprocess.run(e, shell=True).returncode:
                sys.exit("échec : " + e)
