"""Asset Manager de MIRA 3D STUDIO.

Catalogue : assets/catalogue.json (source de vérité, versionnée) + index SQLite (cache/assets/index.sqlite) pour chercher.
Chaque ressource garde sa provenance et sa licence (vérifiée ou non, avec la preuve), et un statut :
  catalogue → telecharge → importe (testé dans Blender) → valide (utilisé dans un rendu qui a passé le contrôle qualité)
Aucune bibliothèque entière n'est téléchargée : seulement les ressources demandées.

  python3 -m mira3d.assets chercher [--texte X] [--type T] [--source S] [--statut S]
  python3 -m mira3d.assets distant polyhaven hdris night         (catalogue sans télécharger)
  python3 -m mira3d.assets telecharger ID [ID…]
  python3 -m mira3d.assets licences                                (régénère assets/LICENCES.md)
  python3 -m mira3d.assets mission1                                (catalogue initial + bureau holographique)"""
import argparse
import glob
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
import zipfile

from .commun import CACHE, RACINE, ecrire_json

CATALOGUE = os.path.join(RACINE, "assets", "catalogue.json")
SOURCES = json.load(open(os.path.join(RACINE, "assets", "sources.json")))
DOSSIER = os.path.join(CACHE, "assets")
UA = {"User-Agent": "MIRA-3D-STUDIO/1.0 (studio d'animation, usage CC0 respectueux)"}
JOURNAL = []


def log(*a):
    msg = " ".join(str(x) for x in a); print(msg, flush=True); JOURNAL.append(f"{time.strftime('%H:%M:%S')} {msg}")


def _get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def _json(url):
    return json.loads(_get(url).decode())


def _sha(f):
    return hashlib.sha1(open(f, "rb").read()).hexdigest()[:16]


# ---------------- catalogue + index
def charger():
    return json.load(open(CATALOGUE)) if os.path.exists(CATALOGUE) else {"assets": {}}


def sauver(cat):
    cat["maj"] = time.strftime("%Y-%m-%d %H:%M:%S")
    ecrire_json(CATALOGUE, cat)


def ajouter(cat, a):
    ancien = cat["assets"].get(a["id"], {})
    for cle in ("statut", "fichiers", "tests", "apercu", "telecharge_le"):
        if cle in ancien and cle not in a:
            a[cle] = ancien[cle]
    a.setdefault("statut", "catalogue")
    cat["assets"][a["id"]] = {**ancien, **a}
    return cat["assets"][a["id"]]


def index(cat=None):
    cat = cat or charger(); os.makedirs(DOSSIER, exist_ok=True)
    db = sqlite3.connect(os.path.join(DOSSIER, "index.sqlite"))
    db.execute("DROP TABLE IF EXISTS assets")
    db.execute("CREATE TABLE assets (id TEXT PRIMARY KEY, source TEXT, type TEXT, titre TEXT, tags TEXT, personnage TEXT, "
               "mouvement TEXT, style TEXT, licence TEXT, licence_verifiee INT, statut TEXT, format TEXT, json TEXT)")
    for a in cat["assets"].values():
        db.execute("INSERT INTO assets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (a["id"], a["source"], a["type"], a.get("titre", ""), " ".join(a.get("tags", [])), a.get("personnage", ""),
                    a.get("mouvement", ""), a.get("style", ""), a["licence"]["nom"], int(bool(a["licence"].get("verifiee"))),
                    a["statut"], a.get("format", ""), json.dumps(a, ensure_ascii=False)))
    db.commit()
    return db


def chercher(texte=None, type_=None, source=None, statut=None, personnage=None, mouvement=None, style=None):
    db = index(); q = "SELECT json FROM assets WHERE 1=1"; v = []
    for col, val in (("type", type_), ("source", source), ("statut", statut), ("personnage", personnage),
                     ("mouvement", mouvement), ("style", style)):
        if val:
            q += f" AND {col} = ?"; v.append(val)
    if texte:
        q += " AND (titre LIKE ? OR tags LIKE ? OR id LIKE ?)"; v += [f"%{texte}%"] * 3
    return [json.loads(r[0]) for r in db.execute(q + " ORDER BY id", v)]


def licence(source, verifiee=False, preuve=None, nom=None):
    s = SOURCES[source]
    return {"nom": nom or s["licence"], "url": s["url_licence"], "verifiee": verifiee, "preuve": preuve,
            "verifiee_le": time.strftime("%Y-%m-%d") if verifiee else None}


# ---------------- connecteurs
class PolyHaven:
    TYPES = {"hdris": "hdri", "textures": "materiau", "models": "modele"}

    def distant(self, cat, type_ph, mots, limite=6):
        data = _json(f"https://api.polyhaven.com/assets?t={type_ph}")
        trouves = []
        for ident, info in data.items():
            texte = " ".join([ident, info.get("name", "")] + info.get("tags", []) + info.get("categories", [])).lower()
            if all(m.lower() in texte for m in mots):
                trouves.append((info.get("download_count", 0), ident, info))
        for _, ident, info in sorted(trouves, reverse=True)[:limite]:
            ajouter(cat, {"id": f"polyhaven/{ident}", "source": "polyhaven", "type": self.TYPES[type_ph], "titre": info.get("name"),
                          "tags": info.get("tags", []) + info.get("categories", []), "style": "realiste",
                          "auteurs": list((info.get("authors") or {}).keys()), "url": f"https://polyhaven.com/a/{ident}",
                          "licence": licence("polyhaven", True, "Toutes les ressources Poly Haven sont CC0 (polyhaven.com/license)"),
                          "format": {"hdri": "hdr", "materiau": "jpg", "modele": "gltf"}[self.TYPES[type_ph]], "ph_type": type_ph})
        log(f"Poly Haven {type_ph} {mots} : {len(trouves)} trouvé(s), {min(len(trouves), limite)} catalogué(s)")
        return [f"polyhaven/{i}" for _, i, _ in sorted(trouves, reverse=True)[:limite]]

    def telecharger(self, a, res="1k"):
        ident = a["id"].split("/", 1)[1]; d = os.path.join(DOSSIER, "polyhaven", ident); os.makedirs(d, exist_ok=True)
        f = _json(f"https://api.polyhaven.com/files/{ident}"); cibles = []
        if a["type"] == "hdri":
            c = f["hdri"][res].get("hdr") or f["hdri"][res]["exr"]; cibles.append((c["url"], os.path.join(d, os.path.basename(c["url"]))))
        elif a["type"] == "materiau":
            for carte in ("Diffuse", "nor_gl", "Rough", "AO", "Displacement"):
                if carte in f and res in f[carte]:
                    c = f[carte][res].get("jpg") or f[carte][res].get("png"); cibles.append((c["url"], os.path.join(d, os.path.basename(c["url"]))))
        else:
            c = f["gltf"][res]["gltf"]; cibles.append((c["url"], os.path.join(d, os.path.basename(c["url"]))))
            for chemin, inc in c.get("include", {}).items():
                cibles.append((inc["url"], os.path.join(d, chemin)))
        for url, dest in cibles:
            if not os.path.exists(dest):
                os.makedirs(os.path.dirname(dest), exist_ok=True); open(dest, "wb").write(_get(url, 300))
        return [cibles[0][1]] + [c[1] for c in cibles[1:]]


class Kenney:
    def _pack(self, pack):
        d = os.path.join(DOSSIER, "kenney", "_packs"); os.makedirs(d, exist_ok=True)
        z = os.path.join(d, f"{pack}.zip"); preuve = None
        page = _get(f"https://kenney.nl/assets/{pack}").decode("utf-8", "ignore")
        if re.search(r"CC0|Creative Commons Zero|public domain", page, re.I):
            preuve = f"mention CC0 trouvée sur https://kenney.nl/assets/{pack} le {time.strftime('%Y-%m-%d')}"
        if not os.path.exists(z):
            liens = re.findall(r"https://kenney\.nl/media/pages/assets/[^\"' ]+?\.zip", page)
            if not liens:
                raise RuntimeError(f"lien de téléchargement introuvable sur la page du pack {pack}")
            open(z, "wb").write(_get(liens[0], 300)); log(f"Kenney : pack {pack} téléchargé ({os.path.getsize(z) // 1024} Ko)")
        return z, preuve

    def distant(self, cat, pack, mots_cles=None):
        z, preuve = self._pack(pack); ids = []
        with zipfile.ZipFile(z) as zf:
            glbs = [n for n in zf.namelist() if n.lower().endswith(".glb")]
        for n in glbs:
            nom = os.path.splitext(os.path.basename(n))[0]
            if mots_cles and not any(m.lower() in nom.lower() for m in mots_cles):
                continue
            tags = re.findall(r"[A-Z]?[a-z]+", nom)
            a = ajouter(cat, {"id": f"kenney/{pack}/{nom}", "source": "kenney", "type": "modele", "titre": nom, "tags": [t.lower() for t in tags] + [pack],
                              "style": "low-poly", "url": f"https://kenney.nl/assets/{pack}", "format": "glb", "zip_chemin": n,
                              "licence": licence("kenney", bool(preuve), preuve)})
            ids.append(a["id"])
        log(f"Kenney {pack} : {len(glbs)} modèles GLB dans le pack, {len(ids)} catalogués")
        return ids

    def telecharger(self, a, res=None):
        pack = a["id"].split("/")[1]; z, _ = self._pack(pack)
        d = os.path.join(DOSSIER, "kenney", pack); os.makedirs(d, exist_ok=True); dest = os.path.join(d, os.path.basename(a["zip_chemin"]))
        if not os.path.exists(dest):
            with zipfile.ZipFile(z) as zf:
                open(dest, "wb").write(zf.read(a["zip_chemin"]))
        return [dest]


class AmbientCG:
    def distant(self, cat, mots, limite=4):
        data = _json(f"https://ambientcg.com/api/v2/full_json?type=Material&q={'+'.join(mots)}&limit={limite}&include=downloadData,tagData")
        ids = []
        for x in data.get("foundAssets", []):
            a = ajouter(cat, {"id": f"ambientcg/{x['assetId']}", "source": "ambientcg", "type": "materiau", "titre": x.get("displayName", x["assetId"]),
                              "tags": x.get("tags", []), "style": "realiste", "url": f"https://ambientcg.com/view?id={x['assetId']}", "format": "jpg",
                              "licence": licence("ambientcg", True, "Toutes les ressources ambientCG sont CC0 (docs.ambientcg.com/license)")})
            ids.append(a["id"])
        log(f"ambientCG {mots} : {len(ids)} catalogué(s)")
        return ids

    def telecharger(self, a, res="1K-JPG"):
        ident = a["id"].split("/", 1)[1]; d = os.path.join(DOSSIER, "ambientcg", ident); os.makedirs(d, exist_ok=True)
        if not glob.glob(os.path.join(d, "*.jpg")):
            data = _json(f"https://ambientcg.com/api/v2/full_json?id={ident}&include=downloadData")
            dl = [x for x in data["foundAssets"][0]["downloadFolders"]["default"]["downloadFiletypeCategories"]["zip"]["downloads"]
                  if x["attribute"] == res][0]
            with zipfile.ZipFile(io.BytesIO(_get(dl["downloadLink"], 300))) as zf:
                zf.extractall(d)
        return sorted(glob.glob(os.path.join(d, "*.jpg")))


class CMU:
    """Quelques clips choisis (pas la base entière). Les conversions BVH viennent de miroirs publics : provenance notée."""
    CLIPS = {"02_01": ("marche", "marche normale"), "16_15": ("marche", "marche lente"), "143_19": ("salut", "salue de la main"),
             "143_04": ("geste", "parle avec les mains"), "13_29": ("attente", "attend, regarde autour")}
    MIROIRS = ["https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/{s:03d}/{c}.bvh",
               "https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/{s:02d}/{c}.bvh"]

    def distant(self, cat):
        ids = []
        for c, (mouv, titre) in self.CLIPS.items():
            a = ajouter(cat, {"id": f"cmu/{c}", "source": "cmu_mocap", "type": "mouvement", "titre": titre, "mouvement": mouv,
                              "tags": [mouv, "mocap", "humain"], "style": "realiste", "url": f"http://mocap.cs.cmu.edu/search.php?subjectnumber={c.split('_')[0]}",
                              "format": "bvh", "licence": licence("cmu_mocap", True, "Conditions de la FAQ CMU (usage libre, revente des données brutes interdite)")})
            ids.append(a["id"])
        return ids

    def telecharger(self, a, res=None):
        c = a["id"].split("/")[1]; s = int(c.split("_")[0]); d = os.path.join(DOSSIER, "cmu"); os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, f"{c}.bvh")
        if not os.path.exists(dest):
            erreurs = []
            for m in self.MIROIRS:
                url = m.format(s=s, c=c)
                try:
                    data = _get(url, 120)
                    if not data.startswith(b"HIERARCHY"):
                        raise RuntimeError("pas un fichier BVH")
                    open(dest, "wb").write(data); a["provenance_fichier"] = url; break
                except Exception as e:
                    erreurs.append(f"{url} : {str(e)[:80]}")
            else:
                raise RuntimeError("aucun miroir BVH : " + " | ".join(erreurs))
        return [dest]


class Rhubarb:
    def distant(self, cat):
        a = ajouter(cat, {"id": "rhubarb/linux", "source": "rhubarb", "type": "outil_levres", "titre": "Rhubarb Lip Sync (Linux)",
                          "tags": ["levres", "visemes", "audio"], "url": SOURCES["rhubarb"]["site"], "format": "binaire",
                          "licence": licence("rhubarb", False)})
        return [a["id"]]

    def telecharger(self, a, res=None):
        d = os.path.join(DOSSIER, "rhubarb"); os.makedirs(d, exist_ok=True)
        exe = glob.glob(os.path.join(d, "**", "rhubarb"), recursive=True)
        if not exe:
            rel = _json("https://api.github.com/repos/DanielSWolf/rhubarb-lip-sync/releases/latest")
            asset = next(x for x in rel["assets"] if "linux" in x["name"].lower() and x["name"].endswith(".zip"))
            with zipfile.ZipFile(io.BytesIO(_get(asset["browser_download_url"], 300))) as zf:
                zf.extractall(d)
            a["version"] = rel.get("tag_name")
            exe = glob.glob(os.path.join(d, "**", "rhubarb"), recursive=True)
        os.chmod(exe[0], 0o755)
        lic = glob.glob(os.path.join(d, "**", "LICENSE*"), recursive=True)
        if lic and "MIT" in open(lic[0], errors="ignore").read():
            a["licence"] = licence("rhubarb", True, f"fichier {os.path.basename(lic[0])} du paquet officiel : licence MIT")
        return [exe[0]]


CONNECTEURS = {"polyhaven": PolyHaven(), "kenney": Kenney(), "ambientcg": AmbientCG(), "cmu_mocap": CMU(), "rhubarb": Rhubarb()}


def telecharger(cat, ident):
    a = cat["assets"][ident]
    if SOURCES[a["source"]]["mode"] != "auto":
        raise RuntimeError(f"{a['source']} : source manuelle, aucun téléchargement automatique")
    t = time.time()
    fichiers = CONNECTEURS[a["source"]].telecharger(a)
    a["fichiers"] = [os.path.relpath(f, RACINE) for f in fichiers]
    a["sha"] = _sha(fichiers[0]); a["taille_ko"] = sum(os.path.getsize(f) for f in fichiers) // 1024
    a["telecharge_le"] = time.strftime("%Y-%m-%d %H:%M:%S"); a["temps_telechargement_s"] = round(time.time() - t, 1)
    if a["statut"] == "catalogue":
        a["statut"] = "telecharge"
    log(f"téléchargé {ident} ({a['taille_ko']} Ko, {a['temps_telechargement_s']} s)")
    return a


def ecrire_licences(cat):
    L = ["# Licences et provenance des ressources", "", "Généré par `python3 -m mira3d.assets licences`. Une ligne par ressource cataloguée.", "",
         "| Ressource | Source | Licence | Vérifiée | Preuve | Statut |", "|---|---|---|---|---|---|"]
    for a in sorted(cat["assets"].values(), key=lambda x: x["id"]):
        li = a["licence"]
        L.append(f"| [{a['id']}]({a.get('url', '')}) | {SOURCES[a['source']]['nom']} | [{li['nom']}]({li['url']}) | "
                 f"{'oui' if li.get('verifiee') else 'non'} | {li.get('preuve') or ''} | {a['statut']} |")
    L += ["", "## Crédits", "", "- Motion capture : The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217.",
          "- Poly Haven, Kenney, ambientCG : CC0, crédit facultatif mais mérité."]
    open(os.path.join(RACINE, "assets", "LICENCES.md"), "w").write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action"); ap.add_argument("args", nargs="*")
    ap.add_argument("--texte"); ap.add_argument("--type"); ap.add_argument("--source"); ap.add_argument("--statut")
    a = ap.parse_args(); cat = charger()
    if a.action == "chercher":
        for x in chercher(a.texte, a.type, a.source, a.statut):
            print(f"{x['id']:45} {x['type']:12} {x['statut']:11} {x['licence']['nom']}")
    elif a.action == "distant":
        src = a.args[0]
        if src == "polyhaven":
            CONNECTEURS[src].distant(cat, a.args[1], a.args[2:])
        elif src == "kenney":
            CONNECTEURS[src].distant(cat, a.args[1], a.args[2:] or None)
        elif src == "ambientcg":
            CONNECTEURS[src].distant(cat, a.args[1:])
        else:
            CONNECTEURS[src].distant(cat)
        sauver(cat); ecrire_licences(cat)
    elif a.action == "telecharger":
        for i in a.args:
            telecharger(cat, i)
        sauver(cat); ecrire_licences(cat)
    elif a.action == "licences":
        ecrire_licences(cat)
    elif a.action == "mission1":
        from .mission_assets import mission1
        mission1()


if __name__ == "__main__":
    main()
