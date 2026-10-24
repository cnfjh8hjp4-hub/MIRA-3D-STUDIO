"""Render Manager : choisit le profil compatible avec la machine, contrôle la scène (Quality Inspector), mesure le
temps par image, estime la durée totale, demande l'accord si c'est long, rend par blocs avec reprise, ne refait pas
les images déjà validées, assemble le MP4 et écrit le rapport."""
import glob
import hashlib
import json
import os
import shutil
import subprocess
import time

from . import materiel as mat
from . import quality_inspector as qi
from .commun import RACINE, RAPPORTS, blender_bin, ecrire_json, horodatage, lancer

PROFILS = json.load(open(os.path.join(RACINE, "config", "profils.json")))
BLOC = 24  # images par passage de Blender : une interruption ne perd au plus qu'un bloc


class AccordRequis(Exception):
    pass


def resoudre_profil(nom, m, moteur_force=None):
    """Profil réel = réglages du premier moteur préféré qui fonctionne sur cette machine."""
    if nom == "auto":
        nom = "CINEMA" if "cycles_gpu" in m.get("moteurs_ok", []) else "STANDARD"
    P = PROFILS[nom]
    ordre = [moteur_force] if moteur_force else P["preference"]
    for cle in ordre:
        # sans GPU, EEVEE tourne en OpenGL logiciel : mesuré 3 fois plus lent que Cycles CPU (25/10) → ignoré sauf demande
        if cle == "eevee" and not moteur_force and not m.get("gpu"):
            continue
        if cle in m.get("moteurs_ok", []):
            base = "cycles" if cle.startswith("cycles") else "eevee"
            if base not in P:
                continue
            p = dict(P[base]); p["moteur"] = base; p["profil"] = nom
            p["appareil"] = "GPU" if cle == "cycles_gpu" else "CPU"
            if cle == "cycles_gpu":
                p["api_gpu"] = m["moteurs"]["cycles_gpu"]["gpu"][0]["api"]
            p["prefixe"] = m["moteurs"][cle].get("prefixe") or []
            p["accord_requis"] = bool(P.get("accord_requis_sans_gpu") and p["appareil"] == "CPU")
            return p
    raise RuntimeError(f"aucun moteur compatible pour {nom} (disponibles : {m.get('moteurs_ok')})")


def _empreinte(scene, profil):
    """Change si la scène, la bibliothèque ou le profil change : les images d'une ancienne version ne sont jamais réutilisées."""
    h = hashlib.sha1(json.dumps({k: v for k, v in profil.items() if k != "prefixe"}, sort_keys=True).encode())
    for f in [scene] + sorted(glob.glob(os.path.join(RACINE, "bibliotheque", "**", "*.*"), recursive=True)) \
            + sorted(glob.glob(os.path.join(RACINE, "assets", "selection_*.json"))):
        if os.path.isfile(f) and "__pycache__" not in f:
            h.update(open(f, "rb").read())
    return h.hexdigest()[:10]


def _sha(f):
    return hashlib.sha1(open(f, "rb").read()).hexdigest()[:12]


def produire(scene, profil_nom="auto", accord=False, budget_min=None, sans_controle=False, moteur=None, journal_cb=print):
    t0 = time.time()
    scene = os.path.abspath(scene)
    nom = os.path.splitext(os.path.basename(scene))[0]
    m = mat.detecter()
    p = resoudre_profil(profil_nom, m, moteur)
    budget = budget_min if budget_min is not None else PROFILS["budget_minutes_sans_accord"]
    projet = os.path.join(RACINE, "sorties", "projets", f"{nom}_{p['profil']}_{_empreinte(scene, p)}")
    images_dir = os.path.join(projet, "images"); controle_dir = os.path.join(projet, "controle")
    os.makedirs(images_dir, exist_ok=True)
    journal = os.path.join(projet, "rendu.log")
    manifeste_f = os.path.join(projet, "manifeste.json")
    manifeste = json.load(open(manifeste_f)) if os.path.exists(manifeste_f) else {"images": {}}
    rapport = {"scene": os.path.relpath(scene, RACINE), "profil": p["profil"], "moteur": p["moteur"], "appareil": p["appareil"],
               "via_ecran_virtuel": bool(p["prefixe"]), "reglages": {k: v for k, v in p.items() if k not in ("prefixe",)},
               "materiel": {k: m[k] for k in ("cpu", "ram_go", "gpu", "blender", "moteurs_ok")}, "projet": os.path.relpath(projet, RACINE),
               "debut": time.strftime("%Y-%m-%d %H:%M:%S"), "etapes": []}
    journal_cb(f"Profil {p['profil']} → {p['moteur']} {p['appareil']}{' (écran virtuel)' if p['prefixe'] else ''}, "
               f"{p['largeur']}x{p['hauteur']}, {p['echantillons']} échantillons")

    def fin(statut, **x):
        rapport.update(statut=statut, duree_totale_s=round(time.time() - t0, 1), **x)
        ecrire_json(os.path.join(projet, "rapport.json"), rapport)
        _rapport_md(rapport)
        return rapport

    # 1. contrôle qualité avant rendu (images tests au profil final : elles servent aussi à mesurer le temps)
    temps_test = []
    if not sans_controle:
        journal_cb("Contrôle qualité : inspection de la scène et images tests…")
        R = qi.inspecter(scene, p, controle_dir, prefixe=p["prefixe"])
        rapport["controle"] = R.dict()
        temps_test = R.infos.get("temps_images_tests_s", [])
        for d in R.defauts:
            journal_cb(f"  [{d['gravite']}] {d['message']}")
        if R.bloquants:
            journal_cb("Rendu final NON lancé : défauts bloquants.")
            return fin("refuse_controle")
        info = R.infos["inspection"]
    else:
        pj = os.path.join(projet, "profil.json"); ecrire_json(pj, p)
        lancer(p["prefixe"] + [blender_bin(), "-b", "--factory-startup", "-P", scene, "--", "--mode", "inspection",
                               "--profil-json", pj, "--sortie", controle_dir], journal, timeout=900)
        info = json.load(open(os.path.join(controle_dir, "inspection.json")))
    debut, fin_ = info["timeline"]; fps = info["fps"]; meta = info.get("meta", {})
    toutes = list(range(debut, fin_ + 1))

    # 2. reprise : images déjà rendues ET validées gardées ; placeholders vides supprimés
    for f in glob.glob(os.path.join(images_dir, "*.png")):
        if os.path.getsize(f) == 0:
            os.remove(f)
    valides = {int(k) for k, v in manifeste["images"].items()
               if v.get("valide") and os.path.exists(os.path.join(images_dir, f"{int(k):04d}.png"))
               and _sha(os.path.join(images_dir, f"{int(k):04d}.png")) == v.get("sha")}
    restantes = [f for f in toutes if f not in valides]

    # 3. estimation (temps des images tests, sans la première qui inclut la préparation)
    par_image = (sorted(temps_test)[len(temps_test) // 2] if temps_test else None)
    estimation_min = round(par_image * len(restantes) / 60, 1) if par_image else None
    rapport.update(images_total=len(toutes), images_deja_validees=len(valides), images_a_rendre=len(restantes),
                   temps_image_test_s=temps_test, estimation_minutes=estimation_min)
    journal_cb(f"{len(valides)} image(s) déjà validée(s), {len(restantes)} à rendre"
               + (f", environ {par_image:.1f} s par image → estimation {estimation_min} min" if par_image else ""))
    if restantes and not accord:
        if p["accord_requis"]:
            journal_cb("Profil CINEMA sans GPU : accord requis (--accord).")
            return fin("accord_requis", raison="CINEMA sur CPU")
        if estimation_min is not None and estimation_min > budget:
            journal_cb(f"Estimation {estimation_min} min > budget {budget} min : accord requis (--accord).")
            return fin("accord_requis", raison=f"estimation {estimation_min} min > budget {budget} min")

    # 4. rendu par blocs ; Blender ne réécrit pas les images existantes
    pj = os.path.join(projet, "profil.json"); ecrire_json(pj, p)
    t_rendu = time.time(); rendues = 0
    for essai in (1, 2):
        restantes = [f for f in toutes if f not in valides]
        blocs = []
        for f in restantes:
            if blocs and f == blocs[-1][1] + 1 and blocs[-1][1] - blocs[-1][0] + 1 < BLOC:
                blocs[-1][1] = f
            else:
                blocs.append([f, f])
        for a, b in blocs:
            code, sec = lancer(p["prefixe"] + [blender_bin(), "-b", "--factory-startup", "-P", scene, "--", "--mode", "frames",
                                               "--profil-json", pj, "--sortie", images_dir, "--frames", f"{a}-{b}"], journal)
            rapport["etapes"].append({"bloc": f"{a}-{b}", "code": code, "secondes": sec, "essai": essai})
            for f in range(a, b + 1):  # 5. validation image par image
                fp = os.path.join(images_dir, f"{f:04d}.png")
                if not os.path.exists(fp) or os.path.getsize(fp) == 0:
                    continue
                r, defs = qi.analyser_image(fp, {})
                ok = not any(g == "bloquant" for g, _, _ in defs)
                manifeste["images"][str(f)] = {"valide": ok, "sha": _sha(fp), "mesures": r}
                if ok:
                    valides.add(f); rendues += 1
                else:
                    os.remove(fp)  # image défectueuse : refaite au 2e essai
            ecrire_json(manifeste_f, manifeste)
            fait = len(valides); ecoule = time.time() - t_rendu
            reste = (ecoule / max(1, rendues)) * (len(toutes) - fait)
            journal_cb(f"  images {a}-{b} : {fait}/{len(toutes)} validées, reste environ {reste / 60:.1f} min")
        if len(valides) == len(toutes):
            break
    temps = [json.loads(l)["secondes"] for l in open(os.path.join(images_dir, "temps_images.jsonl"))] \
        if os.path.exists(os.path.join(images_dir, "temps_images.jsonl")) else []
    manquantes = [f for f in toutes if f not in valides]
    rapport.update(images_rendues_ce_passage=rendues, temps_rendu_s=round(time.time() - t_rendu, 1),
                   temps_par_image_s={"moyen": round(sum(temps) / len(temps), 2) if temps else None,
                                      "min": min(temps) if temps else None, "max": max(temps) if temps else None})
    if manquantes:
        return fin("incomplet", images_manquantes=manquantes)

    # 6. assemblage MP4
    mp4 = os.path.join(projet, f"{nom}_{p['profil']}.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-start_number", str(debut), "-i", os.path.join(images_dir, "%04d.png")]
    audio = (info.get("audio") or [None])[0]
    if audio and os.path.exists(audio):
        cmd += ["-i", audio, "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-movflags", "+faststart", mp4]
    code, _ = lancer(cmd, journal)
    if code != 0 or not os.path.exists(mp4):
        return fin("echec_assemblage")
    sonde = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                       "stream=codec_name,width,height,nb_frames:format=duration", "-of", "json", mp4],
                                      capture_output=True, text=True).stdout or "{}")
    s = (sonde.get("streams") or [{}])[0]
    video = {"fichier": os.path.relpath(mp4, RACINE), "codec": s.get("codec_name"), "largeur": s.get("width"),
             "hauteur": s.get("height"), "images": int(s.get("nb_frames") or 0),
             "duree_s": round(float(sonde.get("format", {}).get("duration", 0)), 2)}
    planche = os.path.join(projet, "planche.jpg")
    lancer(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", f"select='not(mod(n\\,{max(1, len(toutes) // 6)}))',scale=180:-1,tile=6x1",
            "-frames:v", "1", planche], journal)
    dest = os.path.join(RACINE, "sorties", os.path.basename(mp4)); shutil.copy(mp4, dest)
    journal_cb(f"Vidéo : {os.path.relpath(dest, RACINE)} ({video['largeur']}x{video['hauteur']}, {video['duree_s']} s, {video['codec']})")
    return fin("termine", video=video, copie=os.path.relpath(dest, RACINE))


def _rapport_md(r):
    os.makedirs(RAPPORTS, exist_ok=True)
    L = [f"# Rendu « {os.path.basename(r['scene'])} » : {r['statut']}", "",
         f"- Profil **{r['profil']}**, moteur **{r['moteur']} {r['appareil']}**{' (écran virtuel xvfb)' if r['via_ecran_virtuel'] else ''}",
         f"- Machine : {r['materiel']['cpu']['coeurs']} cœurs, {r['materiel']['ram_go']} Go RAM, GPU : "
         f"{', '.join(g['nom'] for g in r['materiel']['gpu']) or 'aucun'} ; moteurs qui fonctionnent : {', '.join(r['materiel']['moteurs_ok'])}",
         f"- Réglages : {r['reglages'].get('largeur')}x{r['reglages'].get('hauteur')}, {r['reglages'].get('echantillons')} échantillons",
         f"- Images : {r.get('images_total')} au total, {r.get('images_deja_validees')} reprises du cache, {r.get('images_rendues_ce_passage', 0)} rendues",
         f"- Estimation avant rendu : {r.get('estimation_minutes')} min ; temps de rendu réel : {round((r.get('temps_rendu_s') or 0) / 60, 1)} min",
         f"- Temps par image : {r.get('temps_par_image_s')}", f"- Durée totale (contrôle compris) : {round(r['duree_totale_s'] / 60, 1)} min"]
    if r.get("video"):
        v = r["video"]; L.append(f"- **Vidéo** : `{r['copie']}` ({v['largeur']}x{v['hauteur']}, {v['images']} images, {v['duree_s']} s, {v['codec']})")
    c = r.get("controle")
    if c:
        L += ["", "## Contrôle qualité", f"Verdict : **{'validé' if c['valide'] else 'refusé'}**"]
        L += [f"- [{d['gravite']}] {d['message']}" for d in c["defauts"]] or ["- aucun défaut détecté"]
        for a in c.get("analyses", []):
            L.append(f"- {a['image']} : luminance {a['luminance_moyenne']}, contraste {a['contraste']}, "
                     + ", ".join(f"{k} {v}" for k, v in a.items() if k.startswith(("palette", "ecart"))))
        for pers, cr in (c.get("comparaison_references") or {}).items():
            L.append(f"- Référence {pers} : " + (f"similarité des teintes {cr['similarite_teintes']} ({cr['type']})" if cr.get("disponible") else cr["raison"]))
    if r.get("raison"):
        L.append(f"\nAccord requis : {r['raison']}. Relance avec `--accord` si tu es d'accord.")
    txt = "\n".join(L) + "\n"
    open(os.path.join(RAPPORTS, f"{horodatage()}_rendu_{os.path.splitext(os.path.basename(r['scene']))[0]}.md"), "w").write(txt)
    open(os.path.join(RAPPORTS, "dernier_rendu.md"), "w").write(txt)
