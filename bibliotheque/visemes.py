"""Visèmes et synchronisation sur la voix."""
import json
import os

VISEMES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "donnees", "visemes.json")))


def enveloppe_audio(chemin, fps):
    """Ouverture de bouche (0-1) par image, à partir de l'amplitude de la voix (module aud de Blender)."""
    import aud
    import numpy as np
    s = aud.Sound(chemin); d = s.data(); sr = int(s.specs[0])
    m = np.abs(d).mean(axis=1) if d.ndim > 1 else np.abs(d)
    n = int(len(m) / sr * fps)
    env = np.array([m[int(i * sr / fps):int((i + 1) * sr / fps)].mean() for i in range(n)])
    env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
    bas, haut = np.percentile(env, 20), np.percentile(env, 95)
    return list(np.clip((env - bas) / max(1e-6, haut - bas), 0, 1))


def texte_vers_visemes(texte):
    """Suite approximative de visèmes depuis un texte français (sans alignement temporel)."""
    L = VISEMES["lettres"]; t = texte.lower(); out = []; i = 0
    while i < len(t):
        if t[i:i + 2] in L:
            out.append(L[t[i:i + 2]]); i += 2; continue
        if t[i] in L:
            out.append(L[t[i]])
        elif t[i] in " .,;!?":
            out.append("repos")
        i += 1
    return out
