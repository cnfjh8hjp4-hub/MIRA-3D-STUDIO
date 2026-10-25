# Rendu « retarget_cmu.py » : termine

- Profil **PREVIEW**, moteur **cycles CPU**
- Machine : 4 cœurs, 15.6 Go RAM, GPU : aucun ; moteurs qui fonctionnent : cycles, eevee
- Réglages : 360x640, 8 échantillons
- Images : 96 au total, 0 reprises du cache, 96 rendues
- Estimation avant rendu : 3.0 min ; temps de rendu réel : 3.1 min
- Temps par image : {'moyen': 1.87, 'min': 1.835, 'max': 1.93}
- Durée totale (contrôle compris) : 3.2 min
- **Vidéo** : `sorties/retarget_cmu_PREVIEW.mp4` (360x640, 96 images, 4.0 s, h264)

## Contrôle qualité
Verdict : **validé**
- aucun défaut détecté
- test_0001.png : luminance 45.11, contraste 55.15, ecart_fond 0.0, palette_mira 1.0
- test_0048.png : luminance 48.3, contraste 56.86, ecart_fond 0.0, palette_mira 1.0
- test_0096.png : luminance 51.64, contraste 59.15, ecart_fond 0.0, palette_mira 1.0
- Référence mira : similarité des teintes 0.177 (couleurs uniquement (la forme n'est pas comparée))
