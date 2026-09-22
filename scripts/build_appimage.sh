#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
DIST="$ROOT/dist"
BUILD="$ROOT/build/appimage"
APPDIR="$BUILD/UniversalDevManager.AppDir"

echo "=== Building Linux AppImage ==="

echo "Syncing versions from meson.build..."
python3 "$ROOT/scripts/sync_version.py"

# Step 1: PyInstaller one-directory build
python3 -m PyInstaller \
    --clean \
    --noconfirm \
    --onedir \
    --name UniversalDevManager \
    --add-data "$ROOT/logo.png:." \
    --add-data "$ROOT/tools.json:." \
    --add-data "$ROOT/src/udm/assets:src/udm/assets" \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtWidgets \
    --distpath "$BUILD/pyinstaller-dist" \
    --workpath "$BUILD/pyinstaller-work" \
    --specpath "$BUILD" \
    "$ROOT/main.py"

# Step 2: Create AppDir structure
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp -r "$BUILD/pyinstaller-dist/UniversalDevManager/"* "$APPDIR/usr/bin/"

# Desktop entry
cat >"$APPDIR/usr/share/applications/UniversalDevManager.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Universal Dev Manager
Comment=Cross-platform developer tool installer
Exec=UniversalDevManager
Icon=UniversalDevManager
Categories=Development;
Terminal=false
EOF

cp "$APPDIR/usr/share/applications/UniversalDevManager.desktop" "$APPDIR/UniversalDevManager.desktop"

# Copy official application icons
cp "$ROOT/logo.svg" "$APPDIR/UniversalDevManager.svg"
cp "$ROOT/logo.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/UniversalDevManager.svg"
cp "$ROOT/logo.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/UniversalDevManager.png"
cp "$ROOT/logo.png" "$APPDIR/.DirIcon"

# AppRun
cat >"$APPDIR/AppRun" <<'APPRUN'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
exec "${HERE}/usr/bin/UniversalDevManager" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# Step 3: Build AppImage
mkdir -p "$DIST"

if ! command -v appimagetool &>/dev/null; then
    echo "Downloading appimagetool..."
    ARCH="$(uname -m)"
    wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage" \
        -O "$BUILD/appimagetool"
    chmod +x "$BUILD/appimagetool"
    APPIMAGETOOL="$BUILD/appimagetool"
else
    APPIMAGETOOL="appimagetool"
fi

ARCH="$(uname -m)" "$APPIMAGETOOL" "$APPDIR" "$DIST/UniversalDevManager-${ARCH}.AppImage"

echo "=== AppImage created at $DIST/ ==="
