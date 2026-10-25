"""Transcription mot à mot (Whisper, local, gratuit) des fichiers audio d'un dossier → JSON {fichier: [{mot, debut, fin}]}.
Usage : python3 scripts/transcrire.py DOSSIER SORTIE.json [modele]"""
import glob
import json
import os
import sys

from faster_whisper import WhisperModel

dossier, sortie = sys.argv[1], sys.argv[2]
m = WhisperModel(sys.argv[3] if len(sys.argv) > 3 else "small", device="cpu", compute_type="int8")
out = {}
for f in sorted(glob.glob(os.path.join(dossier, "*.wav"))):
    segs, _ = m.transcribe(f, language="fr", word_timestamps=True, vad_filter=False, beam_size=5)
    mots = [{"mot": w.word.strip(), "debut": round(w.start, 2), "fin": round(w.end, 2)} for s in segs for w in (s.words or [])]
    out[os.path.basename(f)] = mots
    print(os.path.basename(f), " ".join(x["mot"] for x in mots), flush=True)
json.dump(out, open(sortie, "w"), indent=1, ensure_ascii=False)
