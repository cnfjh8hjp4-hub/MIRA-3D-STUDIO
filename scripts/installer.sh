#!/usr/bin/env bash
# Installe Blender (headless), FFmpeg et les dépendances Python. Gratuit, sans compte, idempotent.
set -euo pipefail
VERSION="${BLENDER_VERSION:-$(python3 -c "import json;print(json.load(open('config/rendu.json'))['blender_version'])")}"
MAJ="${VERSION%.*}"
DEST="${BLENDER_DIR:-/opt/blender}"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

echo "== Paquets système (FFmpeg et bibliothèques nécessaires à Blender sans écran)"
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq ffmpeg xz-utils curl libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libegl1 \
  libxkbcommon0 libsm6 libice6 xvfb xauth libgl1-mesa-dri libglx-mesa0 > /dev/null

if [ -x "$DEST/blender" ] && "$DEST/blender" --version 2>/dev/null | grep -q "Blender $VERSION"; then
  echo "== Blender $VERSION déjà installé"
else
  echo "== Téléchargement de Blender $VERSION (version LTS officielle, blender.org)"
  TMP="$(mktemp -d)"
  curl -fsSL -o "$TMP/blender.tar.xz" "https://download.blender.org/release/Blender${MAJ}/blender-${VERSION}-linux-x64.tar.xz"
  $SUDO rm -rf "$DEST"; $SUDO mkdir -p "$DEST"
  $SUDO tar -xf "$TMP/blender.tar.xz" -C "$DEST" --strip-components=1
  rm -rf "$TMP"
fi
$SUDO ln -sf "$DEST/blender" /usr/local/bin/blender

echo "== Dépendances Python (tests)"
python3 -m pip install -q --upgrade pip
python3 -m pip install -q -r requirements.txt

mkdir -p sorties rapports
chmod +x studio scripts/*.sh
echo "== Installation terminée"
python3 scripts/verifier.py || echo "(vérification : voir ci-dessus)"
