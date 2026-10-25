"""Registre des modèles et rigs de personnages.
Chaque constructeur renvoie un dict {nom_du_pivot: objet} prêt à animer avec bibliotheque.mouvements."""
from .mannequin_holo import construire as mannequin_holo

REGISTRE = {
    "mannequin_holo": {"construire": mannequin_holo, "palette": "mira", "etat": "prêt (démo, primitives)"},
    "arthemis": {"construire": "arthemis.construire", "palette": "arthemis",
                 "etat": "construite pièce par pièce d'après sa planche (yeux, paupières, bec articulé, ailes) : itérations en cours"},
    "mira": {"construire": "mira_hologramme.construire", "palette": "mira",
             "etat": "modèle TRELLIS (MIT) généré depuis son image officielle : À VALIDER par le propriétaire"},
}
