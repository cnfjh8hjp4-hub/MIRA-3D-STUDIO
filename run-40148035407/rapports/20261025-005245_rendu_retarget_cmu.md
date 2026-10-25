# Rendu « retarget_cmu.py » : termine

- Profil **PREVIEW**, moteur **cycles CPU**
- Machine : 4 cœurs, 15.6 Go RAM, GPU : aucun ; moteurs qui fonctionnent : cycles, eevee
- Réglages : 360x640, 8 échantillons
- Images : 96 au total, 0 reprises du cache, 96 rendues
- Estimation avant rendu : 4.3 min ; temps de rendu réel : 4.4 min
- Temps par image : {'moyen': 2.7, 'min': 2.677, 'max': 2.849}
- Durée totale (contrôle compris) : 4.6 min
- **Vidéo** : `sorties/retarget_cmu_PREVIEW.mp4` (360x640, 96 images, 4.0 s, h264)

## Contrôle qualité
Verdict : **validé**
- aucun défaut détecté
- test_0001.png : luminance 44.85, contraste 55.17, ecart_fond 0.0, palette_mira 1.0
- test_0048.png : luminance 48.12, contraste 57.03, ecart_fond 0.0, palette_mira 1.0
- test_0096.png : luminance 51.39, contraste 59.13, ecart_fond 0.0, palette_mira 1.0
- Référence mira : similarité des teintes 0.176 (couleurs uniquement (la forme n'est pas comparée))
