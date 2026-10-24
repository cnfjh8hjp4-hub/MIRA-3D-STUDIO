"""Mission 1 de la bibliothèque : catalogue initial, téléchargements ciblés, tests d'import dans Blender, aperçus,
bureau holographique rendu avec contrôle qualité, test de retargeting CMU, test de Rhubarb, documentation."""
import json
import os
import re
import shutil
import subprocess
import time
import traceback

from . import assets as A
from .commun import RACINE, blender_bin, ecrire_json

TEMPS = {}
PROBLEMES = []


def etape(nom):
    def deco(fn):
        def f(*a, **k):
            t = time.time(); A.log(f"== {nom}")
            try:
                return fn(*a, **k)
            except Exception as e:
                PROBLEMES.append(f"{nom} : {type(e).__name__}: {e}"); A.log("ÉCHEC", nom, e); traceback.print_exc()
            finally:
                TEMPS[nom] = round(time.time() - t, 1)
        return f
    return deco


def _choisir(ids, *motifs, exclure=()):
    for m in motifs:
        for i in ids:
            n = i.rsplit("/", 1)[-1].lower()
            if re.search(m, n) and not any(re.search(x, n) for x in exclure):
                return i
    return None


def mission1():
    t0 = time.time(); cat = A.charger(); res = {}

    @etape("catalogue : Poly Haven")
    def ph():
        res["hdri"] = A.CONNECTEURS["polyhaven"].distant(cat, "hdris", ["night"], 3)
        A.CONNECTEURS["polyhaven"].distant(cat, "hdris", ["studio"], 2)
        for mots in (["desk"], ["chair"], ["lamp"], ["plant"], ["book"]):
            A.CONNECTEURS["polyhaven"].distant(cat, "models", mots, 2)
        A.CONNECTEURS["polyhaven"].distant(cat, "textures", ["metal", "dark"], 2)
    ph()

    @etape("catalogue : Kenney (Furniture Kit)")
    def ke():
        res["kenney"] = A.CONNECTEURS["kenney"].distant(cat, "furniture-kit",
                                                         ["desk", "chair", "computer", "laptop", "lamp", "plant", "book", "monitor", "keyboard", "mouse"])
    ke()

    @etape("catalogue : ambientCG")
    def amb():
        A.CONNECTEURS["ambientcg"].distant(cat, ["metal", "painted"], 2)
    amb()

    @etape("catalogue : CMU et Rhubarb + sources manuelles")
    def anim():
        res["cmu"] = A.CONNECTEURS["cmu_mocap"].distant(cat); A.CONNECTEURS["rhubarb"].distant(cat)
    anim()
    A.sauver(cat)

    # sélection du bureau (Kenney) et de l'éclairage (Poly Haven)
    k = res.get("kenney") or []
    selection = {"bureau": _choisir(k, r"^desk$", r"^desk", exclure=(r"corner", r"lamp")),
                 "chaise": _choisir(k, r"^chairdesk", r"chair.*desk", r"^chair"),
                 "ecran": _choisir(k, r"computerscreen", r"monitor", r"screen"),
                 "clavier": _choisir(k, r"keyboard"), "souris": _choisir(k, r"mouse"),
                 "lampe": _choisir(k, r"lamp.*table", r"lamp"), "plante": _choisir(k, r"plant"), "livres": _choisir(k, r"^books?$", r"book")}
    A.log("sélection bureau :", selection)
    hdri = (res.get("hdri") or [None])[0]
    a_telecharger = [i for i in selection.values() if i] + ([hdri] if hdri else []) + (res.get("cmu") or []) + ["rhubarb/linux"]
    a_telecharger += [i for i in cat["assets"] if i.startswith(("ambientcg/",))][:1]
    a_telecharger += [i for i in cat["assets"] if i.startswith("polyhaven/") and cat["assets"][i]["type"] == "modele"][:2]

    @etape("téléchargements ciblés")
    def dl():
        for i in a_telecharger:
            try:
                A.telecharger(cat, i)
            except Exception as e:
                PROBLEMES.append(f"téléchargement {i} : {str(e)[:200]}"); A.log("échec téléchargement", i, e)
    dl(); A.sauver(cat)

    @etape("tests d'import Blender et aperçus")
    def imp():
        os.makedirs(os.path.join(RACINE, "assets", "apercus"), exist_ok=True)
        for i, a in cat["assets"].items():
            if a["statut"] == "catalogue" or not a.get("fichiers") or a["type"] in ("outil_levres",):
                continue
            nom = re.sub(r"[^a-z0-9_-]", "_", i.lower()); png = os.path.join(RACINE, "assets", "apercus", f"{nom}.png")
            js = os.path.join(A.DOSSIER, "tests", f"{nom}.json"); os.makedirs(os.path.dirname(js), exist_ok=True)
            subprocess.run([blender_bin(), "-b", "--factory-startup", "-P", os.path.join(RACINE, "bibliotheque", "apercu_asset.py"), "--",
                            "--fichier", os.path.join(RACINE, a["fichiers"][0]), "--type", a["type"], "--png", png, "--json", js],
                           capture_output=True, timeout=600)
            r = json.load(open(js)) if os.path.exists(js) else {"ok": False, "erreur": "pas de résultat"}
            a["tests"] = {"import_blender": r.get("ok"), "blender": r.get("blender"), "stats": r.get("stats"), "erreur": r.get("erreur"),
                          "secondes": r.get("secondes"), "le": time.strftime("%Y-%m-%d %H:%M")}
            if r.get("ok"):
                a["statut"] = "importe" if a["statut"] in ("telecharge", "catalogue") else a["statut"]
                a["apercu"] = os.path.relpath(png, RACINE)
            else:
                PROBLEMES.append(f"import {i} : {r.get('erreur')}")
            A.log(f"import {i} : {'OK' if r.get('ok') else 'ÉCHEC'} ({r.get('secondes')} s)")
    imp(); A.sauver(cat)

    @etape("Rhubarb sur la voix d'Arthemis")
    def rh():
        a = cat["assets"].get("rhubarb/linux")
        if not a or not a.get("fichiers"):
            raise RuntimeError("Rhubarb non téléchargé")
        voix = os.path.join(RACINE, "scenes", "medias", "arthemis_s06.mp3"); wav = os.path.join(A.DOSSIER, "arthemis_s06.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voix, "-ac", "1", "-ar", "16000", wav], check=True)
        sortie = os.path.join(RACINE, "scenes", "medias", "arthemis_s06.rhubarb.json")
        p = subprocess.run([os.path.join(RACINE, a["fichiers"][0]), "-f", "json", "-o", sortie, wav], capture_output=True, text=True, timeout=600)
        ok = p.returncode == 0 and os.path.exists(sortie)
        a["tests"] = {"execution": ok, "sortie": os.path.relpath(sortie, RACINE) if ok else None, "erreur": p.stderr[-300:] if not ok else None}
        if ok:
            a["statut"] = "importe"; n = len(json.load(open(sortie)).get("mouthCues", []))
            A.log(f"Rhubarb : {n} formes de bouche générées")
        else:
            raise RuntimeError(p.stderr[-300:])
    rh(); A.sauver(cat)

    # bureau holographique
    roles = [(r, i) for r, i in selection.items() if i and cat["assets"][i]["statut"] == "importe"]
    sel = {"objets": [{"role": r, "id": i, "fichier": cat["assets"][i]["fichiers"][0]} for r, i in roles]}
    if hdri and cat["assets"].get(hdri, {}).get("statut") == "importe":
        sel["hdri"] = {"id": hdri, "fichier": cat["assets"][hdri]["fichiers"][0]}
    ecrire_json(os.path.join(RACINE, "assets", "selection_bureau.json"), sel)
    clip = next((i for i in (res.get("cmu") or []) if cat["assets"][i]["statut"] == "importe"), None)
    if clip:
        ecrire_json(os.path.join(RACINE, "assets", "selection_mouvement.json"), {"id": clip, "fichier": cat["assets"][clip]["fichiers"][0]})

    from . import render_manager as rm
    rendus = {}

    @etape("rendu du bureau holographique (PREVIEW, contrôle qualité)")
    def bureau():
        r = rm.produire(os.path.join(RACINE, "scenes", "bureau_holographique.py"), "PREVIEW", accord=True)
        rendus["bureau"] = r
        if r["statut"] == "termine" and r.get("controle", {}).get("valide"):
            for _, i in roles:
                cat["assets"][i]["statut"] = "valide"; cat["assets"][i]["valide_par"] = "rendu bureau_holographique contrôlé"
            if sel.get("hdri"):
                cat["assets"][sel["hdri"]["id"]]["statut"] = "valide"
    if sel["objets"]:
        bureau()
    else:
        PROBLEMES.append("aucun objet importé pour le bureau : rendu non lancé")

    @etape("test de retargeting CMU (PREVIEW)")
    def ret():
        r = rm.produire(os.path.join(RACINE, "scenes", "tests", "retarget_cmu.py"), "PREVIEW", accord=True)
        rendus["retarget"] = r
        if r["statut"] == "termine" and r.get("controle", {}).get("valide"):
            cat["assets"][clip]["statut"] = "valide"; cat["assets"][clip]["valide_par"] = "retargeting contrôlé (mouvement non jugé à l'œil)"
    if clip:
        ret()
    A.sauver(cat); A.ecrire_licences(cat)
    _documenter(cat, selection, rendus, round(time.time() - t0, 1))


def _documenter(cat, selection, rendus, total):
    L = ["# Bibliothèque de ressources : mission 1", "", f"Exécutée le {time.strftime('%Y-%m-%d %H:%M')} UTC, durée totale {round(total / 60, 1)} min.", "",
         "## Ressources cataloguées", "", "| Statut | Nombre |", "|---|---|"]
    from collections import Counter
    for s, n in Counter(a["statut"] for a in cat["assets"].values()).most_common():
        L.append(f"| {s} | {n} |")
    L += ["", "## Ressources utilisées dans le bureau holographique", "", "| Rôle | Ressource | Licence | Import Blender | Polygones |", "|---|---|---|---|---|"]
    for r, i in selection.items():
        if not i:
            L.append(f"| {r} | aucune trouvée | | | |"); continue
        a = cat["assets"][i]; t = a.get("tests") or {}
        L.append(f"| {r} | [{i}]({a.get('url')}) | {a['licence']['nom']} ({'vérifiée' if a['licence'].get('verifiee') else 'non vérifiée'}) | "
                 f"{'OK' if t.get('import_blender') else t.get('erreur') or 'non testé'} | {(t.get('stats') or {}).get('polygones', '')} |")
    L += ["", "## Temps d'exécution", "", "| Étape | Secondes |", "|---|---|"] + [f"| {k} | {v} |" for k, v in TEMPS.items()]
    L += ["", "## Rendus"]
    for k, r in rendus.items():
        L.append(f"- {k} : **{r['statut']}**" + (f", vidéo `{r.get('copie')}`" if r.get("copie") else "")
                 + (f", contrôle {'validé' if r.get('controle', {}).get('valide') else 'refusé'}" if r.get("controle") else "")
                 + (f", {r.get('temps_par_image_s', {}).get('moyen')} s par image" if r.get("temps_par_image_s") else ""))
    L += ["", "## Problèmes rencontrés", ""] + ([f"- {p}" for p in PROBLEMES] or ["- aucun"])
    L += ["", "## Règles respectées", "", "- Aucune bibliothèque entière téléchargée : seulement les ressources sélectionnées (un pack Kenney, des fichiers Poly Haven en 1K, 5 clips CMU).",
          "- « importe » = testé dans Blender ; « valide » = utilisé dans un rendu qui a passé le contrôle qualité.",
          "- Les références visuelles (planches) ne sont jamais traitées comme des modèles 3D.",
          "- Aucun personnage Mira remplacé par un modèle générique : le retargeting est testé sur le mannequin de démonstration.",
          "", "## Journal", "", "```", *A.JOURNAL[-120:], "```"]
    os.makedirs(os.path.join(RACINE, "docs"), exist_ok=True)
    open(os.path.join(RACINE, "docs", "ASSETS.md"), "w").write("\n".join(L) + "\n")
