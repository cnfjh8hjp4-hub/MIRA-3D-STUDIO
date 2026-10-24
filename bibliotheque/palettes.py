import json
import os

_F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "donnees", "palettes.json")
PALETTES = json.load(open(_F))


def hex_vers_lineaire(h, alpha=1.0):
    """Couleur sRGB #rrggbb → RGBA linéaire (ce que Blender attend dans ses nœuds)."""
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, alpha)


def couleur(personnage, cle="principal"):
    v = PALETTES[personnage][cle]
    if not v:
        raise ValueError(f"palette de {personnage} non renseignée ({cle}) : compléter bibliotheque/donnees/palettes.json")
    return hex_vers_lineaire(v)
