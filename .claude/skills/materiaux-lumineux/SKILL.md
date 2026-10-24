---
name: materiaux-lumineux
description: Matériaux holographiques et lumineux (cyan, violet) pour Cycles : contour Fresnel, filaire, lignes de balayage, réseau de constellations, glow.
---

# Matériaux lumineux

## Recettes (nœuds Cycles)
- **Contour** : Layer Weight (Facing) → puissance 2 → force d'émission. Le bord brille, le centre reste discret.
- **Hologramme** : mélange Émission / Transparent piloté par 1 − Facing (centre transparent, bords opaques).
- **Lignes de balayage** : Wave Texture en bandes sur Z, phase pilotée par `frame*0.25`.
- **Filaire** : modificateur Wireframe (`use_replace=False`, `material_offset=1`) avec un matériau d'émission plus fort.
- **Réseau de constellations** : Voronoi « distance to edge » très fin (échelle ≥ 25, épaisseur ≤ 0.02) + points Voronoi.
- **Glow** : compositeur, Glare « Fog Glow » (seuil 0.6 à 0.8). Streaks seulement sur les sources très fortes.

## Couleurs de l'univers
Cyan Mira `#2CE6FF` · violet Arthemis `#5A0CFF` → lavande `#D9B8FF` · fond nuit `#04121a`.
Transformation de vue « Standard » quand une couleur exacte est imposée ; « AgX » pour un rendu cinéma.
