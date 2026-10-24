---
name: controle-qualite
description: Vérifier l'environnement, lancer les tests automatisés et produire les rapports avant de livrer une vidéo.
---

# Contrôle qualité

- `./studio verifier` : Python, Blender (version attendue), FFmpeg, pytest, disque. Rapport `rapports/verification.json`.
- `./studio test` : configuration, devcontainer, absence de secrets, image test (fond #04121a mesuré au pixel),
  MP4 court (H.264, 12 images). Rapport `rapports/dernier_tests.md`.
- Regarder la vidéo (planche d'images) avant de la livrer : membres qui traversent le corps, scintillement, cadrage.
- Aucune clé dans le dépôt : les jetons vont dans les secrets GitHub, jamais dans le code ni dans la conversation.
- Aucune API payante sans l'accord écrit du propriétaire.
