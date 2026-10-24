# MIRA 3D STUDIO

Studio d'animation 3D dans le cloud (Codespaces + Blender sans écran + FFmpeg). Le propriétaire travaille uniquement depuis un iPhone : réponds en français, explique les actions à faire depuis Safari ou l'app GitHub.

- Commande unique : `./studio materiel|inspecter|produire|demo|polyhaven|gpu-externe|test|verifier` (voir README).
- Pipeline : `mira3d/` (Render Manager, Quality Inspector, détection matériel) ; `bibliotheque/` (modules Blender réutilisables) ; profils dans `config/profils.json`.
- Les 7 Skills du studio sont dans `.claude/skills/`.
- Interdits : API payante de génération vidéo, service payant sans accord, secret dans le dépôt, prétendre avoir rendu sans MP4 ni rapport.
- Sources dans `scenes/`, `config/`, `scripts/` ; vidéos dans `sorties/` (branche `resultats` pour les rendus GitHub) ; rapports dans `rapports/`.
