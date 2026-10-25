# Bibliothèque de ressources : mission 1

Exécutée le 2026-10-25 00:12 UTC, durée totale 12.2 min.

## Ressources cataloguées

| Statut | Nombre |
|---|---|
| catalogue | 36 |
| valide | 10 |
| importe | 8 |

## Ressources utilisées dans le bureau holographique

| Rôle | Ressource | Licence | Import Blender | Polygones |
|---|---|---|---|---|
| bureau | [kenney/furniture-kit/desk](https://kenney.nl/assets/furniture-kit) | CC0 1.0 (vérifiée) | OK | 198 |
| chaise | [kenney/furniture-kit/chairDesk](https://kenney.nl/assets/furniture-kit) | CC0 1.0 (vérifiée) | OK | 588 |
| ecran | [kenney/furniture-kit/computerScreen](https://kenney.nl/assets/furniture-kit) | CC0 1.0 (vérifiée) | OK | 72 |
| clavier | [kenney/furniture-kit/computerKeyboard](https://kenney.nl/assets/furniture-kit) | CC0 1.0 (vérifiée) | OK | 32 |
| souris | [kenney/furniture-kit/computerMouse](https://kenney.nl/assets/furniture-kit) | CC0 1.0 (vérifiée) | OK | 71 |
| lampe | [kenney/furniture-kit/lampRoundTable](https://kenney.nl/assets/furniture-kit) | CC0 1.0 (vérifiée) | OK | 76 |
| plante | [kenney/furniture-kit/plantSmall1](https://kenney.nl/assets/furniture-kit) | CC0 1.0 (vérifiée) | OK | 102 |
| livres | [kenney/furniture-kit/books](https://kenney.nl/assets/furniture-kit) | CC0 1.0 (vérifiée) | OK | 62 |

## Temps d'exécution

| Étape | Secondes |
|---|---|
| catalogue : Poly Haven | 0.9 |
| catalogue : Kenney (Furniture Kit) | 2.3 |
| catalogue : ambientCG | 1.1 |
| catalogue : CMU et Rhubarb + sources manuelles | 0.0 |
| téléchargements ciblés | 12.4 |
| tests d'import Blender et aperçus | 24.1 |
| Rhubarb sur la voix d'Arthemis | 19.4 |
| rendu du bureau holographique (PREVIEW, contrôle qualité) | 477.5 |
| test de retargeting CMU (PREVIEW) | 191.5 |

## Rendus
- bureau : **termine**, vidéo `sorties/bureau_holographique_PREVIEW.mp4`, contrôle validé, 3.82 s par image
- retarget : premier essai **raté visuellement** (mannequin figé), corrigé : 2e essai validé avec mesure d'amplitude (bras 40°, buste 16°), jambes non transférées

## Problèmes rencontrés

- Retargeting CMU : le contrôle qualité a validé l'image, mais en regardant la vidéo le mannequin restait figé bras en croix (l'armature était cachée pendant le transfert, donc jamais évaluée). Le clip est repassé de « valide » à « importe ». Correctif : armature visible pendant le transfert, première image (pose en T) sautée, et contrôle automatique d'amplitude du mouvement (refus sous 5°).
- Leçon : le contrôle qualité ne juge pas encore le mouvement ; une validation de mouvement exige maintenant une mesure d'amplitude.

## Règles respectées

- Aucune bibliothèque entière téléchargée : seulement les ressources sélectionnées (un pack Kenney, des fichiers Poly Haven en 1K, 5 clips CMU).
- « importe » = testé dans Blender ; « valide » = utilisé dans un rendu qui a passé le contrôle qualité.
- Les références visuelles (planches) ne sont jamais traitées comme des modèles 3D.
- Aucun personnage Mira remplacé par un modèle générique : le retargeting est testé sur le mannequin de démonstration.

## Journal

```
00:00:48 == catalogue : Poly Haven
00:00:49 Poly Haven hdris ['night'] : 61 trouvé(s), 3 catalogué(s)
00:00:49 Poly Haven hdris ['studio'] : 101 trouvé(s), 2 catalogué(s)
00:00:49 Poly Haven models ['desk'] : 7 trouvé(s), 2 catalogué(s)
00:00:49 Poly Haven models ['chair'] : 24 trouvé(s), 2 catalogué(s)
00:00:49 Poly Haven models ['lamp'] : 14 trouvé(s), 2 catalogué(s)
00:00:49 Poly Haven models ['plant'] : 67 trouvé(s), 2 catalogué(s)
00:00:49 Poly Haven models ['book'] : 10 trouvé(s), 2 catalogué(s)
00:00:49 Poly Haven textures ['metal', 'dark'] : 0 trouvé(s), 0 catalogué(s)
00:00:49 == catalogue : Kenney (Furniture Kit)
00:00:52 Kenney : pack furniture-kit téléchargé (5010 Ko)
00:00:52 Kenney furniture-kit : 140 modèles GLB dans le pack, 31 catalogués
00:00:52 == catalogue : ambientCG
00:00:53 ambientCG ['metal', 'painted'] : 2 catalogué(s)
00:00:53 == catalogue : CMU et Rhubarb + sources manuelles
00:00:53 sélection bureau : {'bureau': 'kenney/furniture-kit/desk', 'chaise': 'kenney/furniture-kit/chairDesk', 'ecran': 'kenney/furniture-kit/computerScreen', 'clavier': 'kenney/furniture-kit/computerKeyboard', 'souris': 'kenney/furniture-kit/computerMouse', 'lampe': 'kenney/furniture-kit/lampRoundTable', 'plante': 'kenney/furniture-kit/plantSmall1', 'livres': 'kenney/furniture-kit/books'}
00:00:53 == téléchargements ciblés
00:00:53 téléchargé kenney/furniture-kit/desk (14 Ko, 0.7 s)
00:00:54 téléchargé kenney/furniture-kit/chairDesk (38 Ko, 0.6 s)
00:00:55 téléchargé kenney/furniture-kit/computerScreen (6 Ko, 0.5 s)
00:00:55 téléchargé kenney/furniture-kit/computerKeyboard (3 Ko, 0.7 s)
00:00:56 téléchargé kenney/furniture-kit/computerMouse (5 Ko, 0.7 s)
00:00:56 téléchargé kenney/furniture-kit/lampRoundTable (6 Ko, 0.5 s)
00:00:57 téléchargé kenney/furniture-kit/plantSmall1 (8 Ko, 0.7 s)
00:00:58 téléchargé kenney/furniture-kit/books (6 Ko, 0.7 s)
00:00:58 téléchargé polyhaven/moonless_golf (1633 Ko, 0.2 s)
00:00:58 téléchargé cmu/02_01 (253 Ko, 0.2 s)
00:00:59 téléchargé cmu/16_15 (345 Ko, 0.3 s)
00:00:59 téléchargé cmu/143_19 (622 Ko, 0.4 s)
00:00:59 téléchargé cmu/143_04 (808 Ko, 0.4 s)
00:01:00 téléchargé cmu/13_29 (3369 Ko, 0.4 s)
00:01:02 téléchargé rhubarb/linux (7159 Ko, 2.5 s)
00:01:04 téléchargé ambientcg/Metal027 (4857 Ko, 2.0 s)
00:01:05 téléchargé polyhaven/WoodenTable_01 (541 Ko, 0.4 s)
00:01:05 téléchargé polyhaven/desk_lamp_arm_01 (2808 Ko, 0.5 s)
00:01:05 == tests d'import Blender et aperçus
00:01:07 import polyhaven/moonless_golf : OK (1.44 s)
00:01:08 import polyhaven/WoodenTable_01 : OK (0.94 s)
00:01:09 import polyhaven/desk_lamp_arm_01 : OK (0.94 s)
00:01:11 import kenney/furniture-kit/books : OK (1.12 s)
00:01:12 import kenney/furniture-kit/chairDesk : OK (1.01 s)
00:01:14 import kenney/furniture-kit/computerKeyboard : OK (0.9 s)
00:01:15 import kenney/furniture-kit/computerMouse : OK (0.96 s)
00:01:16 import kenney/furniture-kit/computerScreen : OK (1.04 s)
00:01:18 import kenney/furniture-kit/desk : OK (1.01 s)
00:01:19 import kenney/furniture-kit/lampRoundTable : OK (0.98 s)
00:01:20 import kenney/furniture-kit/plantSmall1 : OK (1.0 s)
00:01:22 import ambientcg/Metal027 : OK (0.92 s)
00:01:23 import cmu/02_01 : OK (0.91 s)
00:01:24 import cmu/16_15 : OK (0.95 s)
00:01:26 import cmu/143_19 : OK (1.04 s)
00:01:27 import cmu/143_04 : OK (1.1 s)
00:01:29 import cmu/13_29 : OK (1.81 s)
00:01:29 == Rhubarb sur la voix d'Arthemis
00:01:49 Rhubarb : 31 formes de bouche générées
00:01:49 == rendu du bureau holographique (PREVIEW, contrôle qualité)
00:09:46 == test de retargeting CMU (PREVIEW)
```
