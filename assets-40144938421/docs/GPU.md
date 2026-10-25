# Serveur GPU (facultatif, non activé)

Le studio fonctionne entièrement en CPU (Codespaces, GitHub Actions). Le GPU n'accélère que le rendu final.

Rien n'est loué. Pour l'utiliser un jour, après ton accord explicite :

1. Choisir une machine avec carte NVIDIA (RTX ou A-series) et pilote récent.
2. Ouvrir ce dépôt avec `config/gpu/devcontainer-gpu.json` (ou installer Docker + NVIDIA Container Toolkit).
3. Lancer `./studio demo --preset gpu` : Cycles passe en OptiX, 1080x1920, 128 échantillons.

Ordre de grandeur : la démo de 5 s prend environ 15 à 40 min en preset `standard` sur 2 cœurs CPU,
et 1 à 3 min en preset `gpu` sur une carte récente. Aucun coût tant que rien n'est loué.
