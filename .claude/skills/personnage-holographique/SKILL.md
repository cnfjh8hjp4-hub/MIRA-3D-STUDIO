---
name: personnage-holographique
description: Créer un personnage 3D stylisé de l'univers Mira (Mira, Arthemis, Apollon, Dédale) dans Blender, pièce par pièce et prêt à animer.
---

# Personnage holographique

But : un personnage lisible, élégant, animable, dans l'univers Mira (nuit bleu profond, cyan, violet).

## Méthode
1. Partir des planches de référence (`references/`) : proportions, silhouette, accessoires.
2. Construire en **pièces séparées** (tête, yeux, paupières, bouche ou bec, buste, membres ou ailes, accessoires).
   Chaque partie qui doit bouger seule est un objet ou un groupe de sommets à part.
3. Hiérarchie de pivots (objets vides ou os) : bassin → buste → cou → tête → yeux/bouche.
4. Nommer en français, sans accents : `tete`, `oeil_g`, `bec`, `aile_d`…
5. Script de scène dans `scenes/`, paramétrable (`--sortie`, `--preset`, `--frames`).

## Règles
- Tenues opaques, jamais transparentes ni décolletées ; Mira cadrée des épaules vers le haut par défaut.
- Aucune marque, aucun logo, aucune personne réelle.
- Un modèle généré automatiquement (TRELLIS, Hunyuan3D) sert de référence de volume, pas de modèle final :
  il est grumeleux et les yeux ou la bouche y sont fondus, donc impossibles à animer.
