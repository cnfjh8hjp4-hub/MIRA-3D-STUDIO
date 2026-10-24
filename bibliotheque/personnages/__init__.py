"""Registre des modèles et rigs de personnages.
Chaque constructeur renvoie un dict {nom_du_pivot: objet} prêt à animer avec bibliotheque.mouvements."""
from .mannequin_holo import construire as mannequin_holo

REGISTRE = {
    "mannequin_holo": {"construire": mannequin_holo, "palette": "mira", "etat": "prêt (démo, primitives)"},
    "arthemis": {"construire": None, "palette": "arthemis",
                 "etat": "à construire pièce par pièce (corps, tête, yeux, paupières, bec, aigrettes, ailes)"},
    "mira": {"construire": None, "palette": "mira", "etat": "à construire depuis la planche de référence"},
}
