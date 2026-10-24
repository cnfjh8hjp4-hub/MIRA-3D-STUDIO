---
name: animation-personnage
description: Animer un personnage (tête, corps, bras, ailes, clignement) avec des images clés lissées ou un squelette simple.
---

# Animation de personnage

## Principes
- Images clés en secondes converties en images (`1 + round(t * fps)`), interpolation Bézier « AUTO ».
- Mouvements secondaires permanents : respiration (échelle du buste ±2,5 %), balancement du bassin, regard.
- Une intention par geste : tourner la tête vers ce qu'on regarde, hocher sur les mots forts.
- Pour un maillage d'un seul tenant : groupes de sommets par hauteur (lissage `smoothstep`) + armature tête/corps.

## Gabarits
- Tête : rotation Z ±10 à 30°, X ±8° ; corps : rotation ±10°, respiration 2,4 rad/s.
- Salut : épaule −115° (jamais derrière la tête), avant-bras qui oscille autour de −25°.
- Ailes (Arthemis) : repliées → mi-ouvertes sur un temps fort, retour lent.
