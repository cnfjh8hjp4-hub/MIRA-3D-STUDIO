"""Quality Inspector : contrôles AVANT le rendu final, et contrôle des images rendues.

1. fichier de scène valide          5. images noires, uniformes, surexposées, erreurs du journal
2. ressources (modèles, textures)   6. comparaison colorimétrique aux références (si disponibles)
3. dimensions, caméra, timeline     7. liste des défauts, bloquants ou non
4. images tests                     8. verdict : le rendu final n'est lancé que si rien n'est bloquant

Limite assumée : la comparaison aux références porte sur les COULEURS (teintes dominantes), pas sur la forme.
Aucune ressemblance de forme n'est déclarée validée."""
import colorsys
import glob
import json
import os
import py_compile
import re

from .commun import RACINE, blender_bin, ecrire_json, lancer

PALETTES = json.load(open(os.path.join(RACINE, "bibliotheque", "donnees", "palettes.json")))


class Rapport:
    def __init__(self):
        self.defauts = []; self.infos = {}

    def defaut(self, gravite, code, message):
        self.defauts.append({"gravite": gravite, "code": code, "message": message})

    @property
    def bloquants(self):
        return [d for d in self.defauts if d["gravite"] == "bloquant"]

    def dict(self):
        return {"valide": not self.bloquants, "defauts": self.defauts, **self.infos}


def verifier_fichier(scene, R):
    if not os.path.exists(scene):
        R.defaut("bloquant", "fichier_absent", f"scène introuvable : {scene}"); return False
    if scene.endswith(".py"):
        try:
            py_compile.compile(scene, doraise=True)
        except py_compile.PyCompileError as e:
            R.defaut("bloquant", "script_invalide", str(e)[:300]); return False
    elif scene.endswith(".blend"):
        with open(scene, "rb") as f:
            if f.read(7) != b"BLENDER":
                R.defaut("bloquant", "blend_invalide", "le fichier n'a pas l'en-tête d'un fichier Blender"); return False
    else:
        R.defaut("bloquant", "format_inconnu", "scène attendue en .py ou .blend"); return False
    return True


def erreurs_journal(journal, R):
    if not os.path.exists(journal):
        return
    txt = open(journal, errors="ignore").read()
    if "Traceback (most recent call last)" in txt:
        bloc = txt[txt.rfind("Traceback"):][:800]
        R.defaut("bloquant", "erreur_python", bloc)
    for motif, code in ((r"Error: Cannot read file.*", "fichier_illisible"), (r"Warning: Path '.*' not found", "chemin_introuvable"),
                        (r"Error: .*", "erreur_blender")):
        for m in sorted(set(re.findall(motif, txt)))[:5]:
            if "réglage ignoré" not in m:
                R.defaut("avertissement", code, m[:200])


def controler_inspection(info, profil, R):
    meta = info.get("meta", {})
    if not info.get("camera"):
        R.defaut("bloquant", "pas_de_camera", "aucune caméra active")
    w, h = info["resolution"]
    if (w, h) != (profil["largeur"], profil["hauteur"]):
        R.defaut("bloquant", "dimensions", f"résolution {w}x{h} au lieu de {profil['largeur']}x{profil['hauteur']}")
    if w % 2 or h % 2:
        R.defaut("bloquant", "dimensions_impaires", "le H.264 exige des dimensions paires")
    if meta.get("format") == "9:16" and abs(w / h - 9 / 16) > 0.01:
        R.defaut("avertissement", "format", f"format {w}x{h} différent du 9:16 annoncé")
    debut, fin = info["timeline"]
    if fin < debut:
        R.defaut("bloquant", "timeline_vide", "aucune image dans la timeline")
    attendu = round(meta.get("duree_s", 0) * info["fps"])
    if attendu and fin - debut + 1 != attendu:
        R.defaut("avertissement", "duree", f"{fin - debut + 1} images au lieu de {attendu}")
    for m in info.get("ressources_manquantes", []):
        R.defaut("bloquant", f"{m['type']}_manquant", f"{m['nom']} : {m['chemin']}")
    for c in info.get("cadrage", []):
        if c["objets"] and c["objets_dans_le_champ"] == 0:
            R.defaut("bloquant", "cadrage_vide", f"image {c['image']} : aucun objet dans le champ de la caméra")


def _teintes(img, masque_fond=None):
    """Histogramme de teintes (36 cases de 10°) des pixels colorés et lumineux."""
    import numpy as np
    a = np.asarray(img.convert("RGB").resize((180, 320)), dtype=np.float32) / 255
    mx, mn = a.max(axis=2), a.min(axis=2)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    garde = (s > 0.30) & (mx > 0.25)
    if masque_fond is not None:
        garde &= ~masque_fond
    px = a[garde]
    if len(px) < 50:
        return None, 0
    hsv = np.array([colorsys.rgb_to_hsv(*p) for p in px[:: max(1, len(px) // 4000)]])
    hist, _ = np.histogram(hsv[:, 0] * 360, bins=36, range=(0, 360))
    return hist / max(1, hist.sum()), int(garde.sum())


def analyser_image(chemin, meta=None):
    """Mesures objectives d'une image rendue. Renvoie un dict (et la liste des défauts détectés)."""
    import numpy as np
    from PIL import Image
    im = Image.open(chemin); a = np.asarray(im.convert("RGB"), dtype=np.float32)
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    r = {"image": os.path.basename(chemin), "luminance_moyenne": round(float(lum.mean()), 2),
         "contraste": round(float(lum.std()), 2), "part_noir": round(float((lum < 3).mean()), 4),
         "part_blanc_brule": round(float((a.min(axis=2) > 250).mean()), 4)}
    defauts = []
    if r["luminance_moyenne"] < 2 and r["contraste"] < 2:
        defauts.append(("bloquant", "image_noire", f"{r['image']} est noire"))
    elif r["contraste"] < 1.5:
        defauts.append(("bloquant", "image_uniforme", f"{r['image']} est uniforme (rien de rendu ?)"))
    if r["part_blanc_brule"] > 0.25:
        defauts.append(("avertissement", "surexposition", f"{r['image']} : {r['part_blanc_brule']:.0%} de blancs brûlés"))
    meta = meta or {}
    if meta.get("fond"):
        h = meta["fond"].lstrip("#"); ref = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)
        coins = np.array([a[2, 2], a[2, -3], a[-3, 2], a[-3, -3]])
        ecart = float(np.abs(coins - ref).max(axis=1).min())
        r["ecart_fond"] = round(ecart, 1)
        if ecart > 12:
            defauts.append(("avertissement", "fond", f"{r['image']} : fond éloigné de {meta['fond']} (écart {ecart:.0f})"))
    for pers in meta.get("personnages", []):
        plage = PALETTES.get(pers, {}).get("teinte_dominante_deg")
        if not plage:
            r[f"palette_{pers}"] = "palette non renseignée"; continue
        hist, n = _teintes(im)
        if hist is None:
            defauts.append(("avertissement", "palette", f"{r['image']} : trop peu de pixels colorés pour juger la palette de {pers}"))
            continue
        a0, a1 = plage; idx = [i for i in range(36) if a0 <= i * 10 + 5 <= a1]
        part = float(hist[idx].sum()); r[f"palette_{pers}"] = round(part, 3)
        if part < 0.5:
            defauts.append(("avertissement", "palette", f"{r['image']} : {part:.0%} des pixels colorés dans la teinte officielle de {pers} ({a0}-{a1}°)"))
    return r, defauts


def comparer_references(images, personnages):
    """Comparaison colorimétrique (intersection d'histogrammes de teintes) avec references/<personnage>/*."""
    from PIL import Image
    out = {}
    for pers in personnages:
        refs = sorted(glob.glob(os.path.join(RACINE, "references", pers, "*.png")) + glob.glob(os.path.join(RACINE, "references", pers, "*.jpg")))
        if not refs:
            out[pers] = {"disponible": False, "raison": f"aucune image dans references/{pers}/"}; continue
        h_ref = [h for h, _ in (_teintes(Image.open(f)) for f in refs) if h is not None]
        h_img = [h for h, _ in (_teintes(Image.open(f)) for f in images) if h is not None]
        if not h_ref or not h_img:
            out[pers] = {"disponible": False, "raison": "pas assez de pixels colorés"}; continue
        import numpy as np
        hr, hi = np.mean(h_ref, axis=0), np.mean(h_img, axis=0)
        out[pers] = {"disponible": True, "type": "couleurs uniquement (la forme n'est pas comparée)",
                     "similarite_teintes": round(float(np.minimum(hr, hi).sum()), 3), "references": len(refs)}
    return out


def inspecter(scene, profil, dossier, frames_tests=None, prefixe=None, meta_attendue=None):
    """Contrôle complet avant rendu. Écrit dossier/controle.json et renvoie le rapport."""
    os.makedirs(dossier, exist_ok=True)
    R = Rapport(); b = blender_bin(); prefixe = prefixe or []
    if not verifier_fichier(scene, R):
        return R
    pj = os.path.join(dossier, "profil.json"); ecrire_json(pj, profil)
    journal = os.path.join(dossier, "controle.log"); open(journal, "w").close()
    code, sec = lancer(prefixe + [b, "-b", "--factory-startup", "-P", scene, "--", "--mode", "inspection",
                                  "--profil-json", pj, "--sortie", dossier], journal, timeout=900)
    ip = os.path.join(dossier, "inspection.json")
    if code != 0 or not os.path.exists(ip):
        R.defaut("bloquant", "inspection_impossible", f"Blender a échoué pendant l'inspection (code {code})")
        erreurs_journal(journal, R); R.infos["journal"] = journal
        return R
    info = json.load(open(ip)); R.infos["inspection"] = info
    controler_inspection(info, profil, R)
    if R.bloquants:
        erreurs_journal(journal, R); return R
    debut, fin = info["timeline"]
    frames_tests = frames_tests or sorted({debut, (debut + fin) // 2, fin})
    code, sec = lancer(prefixe + [b, "-b", "--factory-startup", "-P", scene, "--", "--mode", "images", "--profil-json", pj,
                                  "--sortie", dossier, "--frames", ",".join(map(str, frames_tests))], journal, timeout=7200)
    erreurs_journal(journal, R)
    images = [os.path.join(dossier, f"test_{f:04d}.png") for f in frames_tests]
    manquantes = [os.path.basename(i) for i in images if not os.path.exists(i)]
    if manquantes:
        R.defaut("bloquant", "rendu_test_echoue", f"images tests non produites : {', '.join(manquantes)} (code {code})")
    analyses = []
    for i in images:
        if os.path.exists(i):
            r, d = analyser_image(i, info.get("meta"))
            analyses.append(r)
            for g, c, m in d:
                R.defaut(g, c, m)
    temps = []
    tf = os.path.join(dossier, "temps_images.jsonl")
    if os.path.exists(tf):
        temps = [json.loads(l)["secondes"] for l in open(tf) if l.strip()]
    R.infos.update({"images_tests": [os.path.basename(i) for i in images if os.path.exists(i)], "analyses": analyses,
                    "temps_images_tests_s": temps, "comparaison_references": comparer_references(
                        [i for i in images if os.path.exists(i)], info.get("meta", {}).get("personnages", [])),
                    "journal": journal})
    ecrire_json(os.path.join(dossier, "controle.json"), R.dict())
    return R
