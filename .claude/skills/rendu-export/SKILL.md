---
name: rendu-export
description: Rendre une scène Blender sans écran et exporter un MP4 H.264, avec les presets CPU économiques du studio.
---

# Rendu et export

Commande unique : `./studio demo` ou `./studio rendre scenes/<scene>.py --preset eco`.

| Preset | Usage | Réglages |
|---|---|---|
| apercu | test en quelques minutes | 360x640, 8 échantillons |
| eco | défaut, CPU économique | 540x960, 16 échantillons, débruitage |
| standard | final Instagram | 1080x1920, 48 échantillons |
| gpu | futur serveur GPU, non loué | 1080x1920, 128 échantillons, OptiX |

- Export direct par Blender : FFMPEG, conteneur MPEG4, codec H264, qualité HIGH, AAC si voix.
- Après rendu : contrôle `ffprobe` (codec, images, durée), vignette JPG, rapport dans `rapports/`.
- Ne jamais annoncer un rendu sans le MP4 et son rapport.
