"""Tests automatisés du studio.
- tests unitaires : sans Blender (profils, analyse d'image, palettes, visèmes, absence de secrets)
- tests d'intégration : avec Blender (sonde matériel, contrôle qualité de la démo, refus d'une scène défectueuse)"""
import json
import os
import re
import subprocess
import sys

import pytest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from mira3d import quality_inspector as qi  # noqa: E402
from mira3d import render_manager as rm  # noqa: E402
from mira3d.commun import blender_bin  # noqa: E402

BLENDER = blender_bin()
avec_blender = pytest.mark.skipif(not BLENDER, reason="Blender absent (lance bash scripts/installer.sh)")

FAUX_CPU = {"moteurs_ok": ["cycles"], "moteurs": {"cycles": {"ok": True, "prefixe": []}}}
FAUX_EEVEE = {"moteurs_ok": ["cycles", "eevee"], "moteurs": {"cycles": {"ok": True}, "eevee": {"ok": True, "prefixe": ["xvfb-run", "-a"]}}}
FAUX_GPU = {"moteurs_ok": ["cycles", "cycles_gpu"], "moteurs": {"cycles": {"ok": True}, "cycles_gpu": {"ok": True, "gpu": [{"api": "OPTIX", "nom": "RTX"}]}}}


def test_profils_et_choix_du_moteur():
    p = rm.resoudre_profil("PREVIEW", FAUX_CPU)
    assert p["moteur"] == "cycles" and p["largeur"] == 360
    p = rm.resoudre_profil("PREVIEW", FAUX_EEVEE)
    assert p["moteur"] == "eevee" and p["prefixe"] == ["xvfb-run", "-a"]
    assert rm.resoudre_profil("auto", FAUX_CPU)["profil"] == "STANDARD"
    c = rm.resoudre_profil("auto", FAUX_GPU)
    assert c["profil"] == "CINEMA" and c["appareil"] == "GPU" and not c["accord_requis"]
    assert rm.resoudre_profil("CINEMA", FAUX_CPU)["accord_requis"] is True


def test_empreinte_change_avec_le_profil(tmp_path):
    s = tmp_path / "s.py"; s.write_text("x=1")
    a = rm._empreinte(str(s), {"echantillons": 8}); b = rm._empreinte(str(s), {"echantillons": 16})
    assert a != b and a == rm._empreinte(str(s), {"echantillons": 8})


def test_inspecteur_detecte_image_noire_et_palette(tmp_path):
    from PIL import Image
    noir = tmp_path / "noir.png"; Image.new("RGB", (90, 160), (0, 0, 0)).save(noir)
    _, d = qi.analyser_image(str(noir), {})
    assert any(c == "image_noire" for _, c, _ in d)
    im = Image.new("RGB", (90, 160), (4, 18, 26))
    for x in range(30, 60):
        for y in range(40, 120):
            im.putpixel((x, y), (44, 230, 255))  # cyan officiel de Mira
    f = tmp_path / "mira.png"; im.save(f)
    r, d = qi.analyser_image(str(f), {"fond": "#04121a", "personnages": ["mira"]})
    assert r["ecart_fond"] <= 1 and r["palette_mira"] > 0.9 and not any(g == "bloquant" for g, _, _ in d)
    r, d = qi.analyser_image(str(f), {"personnages": ["arthemis"]})
    assert any(c == "palette" for _, c, _ in d)  # du cyan n'est pas la palette violette d'Arthemis


def test_comparaison_references_signale_absence():
    out = qi.comparer_references([], ["personnage_inexistant"])
    assert out["personnage_inexistant"]["disponible"] is False


def test_visemes():
    from bibliotheque.visemes import texte_vers_visemes, VISEMES
    assert texte_vers_visemes("papa") == ["MBP", "A", "MBP", "A"]
    assert all(k in VISEMES for k in ("A", "E", "I", "O", "U", "MBP", "FV", "repos"))


def test_configurations_valides():
    p = json.load(open(os.path.join(RACINE, "config", "profils.json")))
    for nom in ("PREVIEW", "STANDARD", "CINEMA"):
        for m in p[nom]["preference"]:
            assert m.split("_")[0] in p[nom]
    json.load(open(os.path.join(RACINE, ".devcontainer", "devcontainer.json")))
    pal = json.load(open(os.path.join(RACINE, "bibliotheque", "donnees", "palettes.json")))
    assert pal["univers"]["fond_nuit"] == "#04121a"


def test_aucun_secret_dans_le_depot():
    motif = re.compile(r"(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}|hf_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{20,}"
                       r"|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
    for dp, dn, fn in os.walk(RACINE):
        dn[:] = [d for d in dn if d not in (".git", "sorties", "cache", "__pycache__", ".pytest_cache")]
        for f in fn:
            if f.endswith((".py", ".json", ".sh", ".yml", ".yaml", ".md", ".txt", ".env")) or f == "studio":
                assert not motif.search(open(os.path.join(dp, f), errors="ignore").read()), f"secret possible dans {f}"


def test_scripts_compilent():
    for dp, dn, fn in os.walk(RACINE):
        dn[:] = [d for d in dn if d not in (".git", "sorties", "cache", "__pycache__")]
        for f in fn:
            if f.endswith(".py") or f == "studio":
                subprocess.run([sys.executable, "-m", "py_compile", os.path.join(dp, f)], check=True)


@avec_blender
def test_detection_materiel():
    from mira3d import materiel
    m = materiel.detecter(rafraichir=True)
    assert m["cpu"]["coeurs"] >= 1 and "cycles" in m["moteurs_ok"], materiel.resume(m)


@avec_blender
def test_controle_qualite_demo(tmp_path):
    from mira3d import materiel
    p = rm.resoudre_profil("PREVIEW", materiel.detecter())
    R = qi.inspecter(os.path.join(RACINE, "scenes", "demo_hologramme.py"), p, str(tmp_path), frames_tests=[1, 60])
    assert not R.bloquants, R.dict()
    assert len(R.infos["analyses"]) == 2


@avec_blender
def test_controle_qualite_refuse_scene_defectueuse(tmp_path):
    from mira3d import materiel
    p = rm.resoudre_profil("PREVIEW", materiel.detecter())
    R = qi.inspecter(os.path.join(RACINE, "scenes", "tests", "scene_vide.py"), p, str(tmp_path))
    codes = {d["code"] for d in R.bloquants}
    assert codes & {"cadrage_vide", "image_noire", "image_uniforme"}, R.dict()
