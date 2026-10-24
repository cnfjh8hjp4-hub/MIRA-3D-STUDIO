# MIRA 3D STUDIO

Studio d'animation 3D autonome dans le cloud : GitHub Codespaces pour travailler, Blender (sans écran) pour la 3D,
FFmpeg pour la vidéo, GitHub Actions pour lancer des rendus depuis un iPhone.

## Depuis l'iPhone

**Lancer un rendu sans rien installer (le plus simple)**
App GitHub ou Safari → dépôt → onglet **Actions** → **Studio (rendu et tests)** → **Run workflow** →
action `demo`, preset `eco` → **Run**. Environ 10 à 20 min plus tard, la vidéo est sur la branche `resultats`
(dossier `run-N/sorties/…/demo_hologramme.mp4`) et en artefact téléchargeable.

**Ouvrir le studio (Codespaces)**
Safari → dépôt → bouton vert **Code** → onglet **Codespaces** → **Create codespace on main**.
La première ouverture installe Blender et FFmpeg (5 à 10 min). Ensuite, dans le terminal :

```
./studio verifier        # versions et dépendances
./studio demo            # génère, rend et exporte la démo de 5 s en MP4
./studio test            # tests automatisés + rapport
```

Pense à arrêter le codespace après usage (Safari → github.com/codespaces → … → Stop) pour garder ton quota gratuit.

## Organisation

| Dossier | Contenu |
|---|---|
| `scenes/` | scripts de scènes Blender (sources) |
| `config/rendu.json` | durée, fond, presets `apercu`, `eco`, `standard`, `gpu` |
| `config/gpu/` | configuration facultative pour un futur serveur GPU (non louée) |
| `scripts/` | installation et vérification |
| `tests/` | tests automatisés |
| `sorties/` | vidéos rendues (non versionnées sur `main`) |
| `rapports/` | rapports de rendu, de tests et de vérification |
| `.claude/skills/` | les 7 Skills du studio (personnage, matériaux, animation, caméra, rendu, voix, contrôle qualité) |
| `.devcontainer/` | configuration Codespaces |

## Règles

Aucune API payante de génération vidéo, aucun service payant installé, aucun secret dans le dépôt.
