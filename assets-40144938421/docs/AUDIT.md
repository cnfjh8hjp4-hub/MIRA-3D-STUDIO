# Audit MIRA 3D STUDIO (25 octobre 2026)

## Outils réellement disponibles (mesurés)
| Outil | État |
|---|---|
| Serveur GitHub Actions (dépôt privé) | 2 cœurs CPU, ~7 Go RAM, aucun GPU, 14 Go de disque libre |
| Blender 4.2.3 LTS sans écran | fonctionne (rendu V1 réel : 120 images, MP4 H.264) |
| Cycles CPU | fonctionne : 8,8 s par image en 540x960, 16 échantillons |
| EEVEE | non vérifié : la sonde (direct puis écran virtuel xvfb) est prête mais n'a pas pu tourner |
| FFmpeg 8.0.1, Python 3.11, pytest | fonctionnent |
| GPU | aucun (préparé en option, rien de loué) |
| Minutes GitHub Actions | ÉPUISÉES pour le compte le 25/10 à 00 h 43 : plus aucun job ne démarre |

## Améliorations prioritaires
1. Débloquer les minutes : rendre ce dépôt public (minutes illimitées et serveurs 4 cœurs), sans aucun secret dedans.
2. Vérifier EEVEE avec écran virtuel : s'il fonctionne, le profil STANDARD devient 5 à 10 fois plus rapide.
3. Reconstruire les personnages pièce par pièce (Arthemis d'abord), avec yeux, paupières et bec séparés.
4. Vrais visèmes : formes de bouche par personnage, pilotées par la voix.
5. Comparaison de forme aux références (aujourd'hui : couleurs seulement).

## Limites restantes
- Render Manager et Quality Inspector écrits et testés hors Blender, mais pas encore exécutés avec Blender (minutes épuisées).
- La comparaison aux références porte sur les couleurs, jamais sur la forme.
- Le personnage de démo est un mannequin en primitives, pas encore un personnage officiel.
- Poly Haven : le script est prêt mais n'a pas encore été essayé (réseau du serveur GitHub nécessaire).
