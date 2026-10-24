# Rendu « demo_hologramme.py » : termine

- Profil **PREVIEW**, moteur **cycles CPU**
- Machine : 4 cœurs, 15.6 Go RAM, GPU : aucun ; moteurs qui fonctionnent : cycles, eevee
- Réglages : 360x640, 8 échantillons
- Images : 120 au total, 0 reprises du cache, 120 rendues
- Estimation avant rendu : 4.8 min ; temps de rendu réel : 4.9 min
- Temps par image : {'moyen': 2.41, 'min': 2.383, 'max': 2.446}
- Durée totale (contrôle compris) : 5.0 min
- **Vidéo** : `sorties/demo_hologramme_PREVIEW.mp4` (360x640, 120 images, 5.0 s, h264)

## Contrôle qualité
Verdict : **validé**
- aucun défaut détecté
- test_0001.png : luminance 83.06, contraste 75.24, ecart_fond 0.0, palette_mira 0.996
- test_0060.png : luminance 93.11, contraste 76.92, ecart_fond 0.0, palette_mira 1.0
- test_0120.png : luminance 105.63, contraste 78.74, ecart_fond 1.0, palette_mira 0.999
- Référence mira : similarité des teintes 0.536 (couleurs uniquement (la forme n'est pas comparée))
