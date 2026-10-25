# Nuit du 25 octobre 2026 : rendus de Mira et d'Arthemis

## Arthemis
| Version | Méthode | Résultat mesuré | Verdict à l'œil |
|---|---|---|---|
| v1 | pièces séparées (primitives) | PREVIEW, 14,7 min (estimé 14,8) | iris blancs, aigrettes en pics, ailes décollées, « verre fissuré » |
| v2 | + écailles de plumes, iris, ailes contre le corps | PREVIEW, 15,7 min | chouette lisible mais dessin animé |
| v3-v4 | iris saturés, tête plus grande, plumes pointues | contrôles STANDARD | motif trop géométrique, doubles contours |
| **B** | modèle TRELLIS (MIT) depuis son image officielle + yeux, paupières et bec articulés ajoutés | **STANDARD 720x1280, 152,9 min (estimé 155,5), voix incluse** | **la plus fidèle à la planche** (sourcils en V, aigrettes, plumes, serres) |

Leçons : des primitives donnent un personnage « jouet » ; un modèle tiré de l'image officielle respecte bien mieux le design.
Les parties qui doivent bouger (yeux, paupières, bec) sont ajoutées par-dessus et placées automatiquement :
yeux = zones claires sous les sourcils, bec = pointe la plus avancée. Bug corrigé : bec attaché aux pieds (matrice non recalculée).

## Mira
| Version | Résultat | Verdict |
|---|---|---|
| mannequin (démo) | STANDARD 26,1 min | personnage générique, pas Mira |
| TRELLIS (MIT) depuis son image officielle | STANDARD 78 min (estimé 78,7) | reconnaissable de loin ; visage grossier en 720p ; ombrage du haut ambigu |
| v2 | haut uniformisé, pantalon sombre, cadrage moins serré | STANDARD 80,4 min (estimé 79,8) ; il reste un ombrage au creux du haut venant de la géométrie : à valider, pas à publier |

## Ce qui manque pour atteindre le niveau Kling
1. **Des modèles 3D propres des personnages** : les modèles automatiques (TRELLIS) sont simplifiés (≈ 6 000 sommets pour Mira, visage flou).
   Pistes gratuites : vues multiples cohérentes du personnage (face, profil, dos, trois-quarts) pour TRELLIS multi-images ;
   ou un sculpteur 3D humain (payant, sur accord).
2. **Une bouche et des yeux modélisés pour Mira** (visèmes) : aujourd'hui sa bouche ne peut pas bouger.
3. **Un GPU** pour le profil CINEMA (1080x1920, 128 échantillons) : sur CPU, Arthemis STANDARD = 46 s par image ; CINEMA serait 4 à 8 fois plus long.
4. **Un rig complet** (os de jambes et bras) pour appliquer les mouvements de la bibliothèque (CMU) aux vrais personnages.
