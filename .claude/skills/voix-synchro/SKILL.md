---
name: voix-synchro
description: Synchroniser la bouche ou le bec d'un personnage sur une voix (ElevenLabs ou autre) et intégrer l'audio dans le MP4.
---

# Voix et synchronisation

1. Charger la voix avec le module `aud` de Blender (`aud.Sound(f).data()`), passer en mono.
2. Enveloppe par image : moyenne de l'amplitude sur 1/fps s, lissage [0.25, 0.5, 0.25],
   normalisation entre le 20e et le 95e centile.
3. Ouverture de bouche ou de bec = enveloppe × amplitude max (bec : 16°), clé à chaque image.
4. Ajouter la voix au séquenceur (`sequences.new_sound`) et exporter en AAC.
5. Visèmes précis (A, E, I, O, U, M/B/P, F/V) : seulement si le personnage a des formes de bouche séparées.

Voix : fichiers fournis par le propriétaire (ElevenLabs). Ne jamais cloner une voix sans accord.
