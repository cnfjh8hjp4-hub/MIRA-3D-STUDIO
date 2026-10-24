# Rendu « demo_hologramme.py » : accord_requis

- Profil **PREVIEW**, moteur **eevee CPU**
- Machine : 4 cœurs, 15.6 Go RAM, GPU : aucun ; moteurs qui fonctionnent : cycles, eevee
- Réglages : 360x640, 16 échantillons
- Images : 120 au total, 0 reprises du cache, 0 rendues
- Estimation avant rendu : 28.4 min ; temps de rendu réel : 0.0 min
- Temps par image : None
- Durée totale (contrôle compris) : 0.9 min

## Contrôle qualité
Verdict : **validé**
- aucun défaut détecté
- test_0001.png : luminance 83.43, contraste 75.68, ecart_fond 0.0, palette_mira 1.0
- test_0060.png : luminance 93.52, contraste 77.25, ecart_fond 0.0, palette_mira 1.0
- test_0120.png : luminance 105.61, contraste 78.98, ecart_fond 1.0, palette_mira 1.0
- Référence mira : similarité des teintes 0.627 (couleurs uniquement (la forme n'est pas comparée))

Accord requis : estimation 28.4 min > budget 20.0 min. Relance avec `--accord` si tu es d'accord.
