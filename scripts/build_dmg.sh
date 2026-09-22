#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
DIST="$ROOT/dist"
BUILD="$ROOT/build/dmg"

echo "=== Building macOS .dmg ==="

echo "Syncing versions from meson.build..."
python3 "$ROOT/scripts/sync_version.py"

# Step 1: PyInstaller .app bundle
python3 -m PyInstaller \
    --clean \
    --noconfirm \
    --onedir \
    --windowed \
    --name "Universal Dev Manager" \
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

# Step 2: Create DMG
mkdir -p "$DIST"
APP_PATH="$BUILD/pyinstaller-dist/Universal Dev Manager.app"

if [ -d "$APP_PATH" ]; then
    DMG_PATH="$DIST/UniversalDevManager.dmg"
    rm -f "$DMG_PATH"

    # Create a temporary DMG directory
    DMG_STAGING="$BUILD/dmg-staging"
    rm -rf "$DMG_STAGING"
    mkdir -p "$DMG_STAGING"
    cp -R "$APP_PATH" "$DMG_STAGING/"
    ln -s /Applications "$DMG_STAGING/Applications"

    hdiutil create \
        -volname "Universal Dev Manager" \
        -srcfolder "$DMG_STAGING" \
        -ov \
        -format UDZO \
        "$DMG_PATH"

    rm -rf "$DMG_STAGING"
    echo "=== DMG created at $DMG_PATH ==="
else
    echo "ERROR: .app bundle not found at $APP_PATH"
    echo "PyInstaller may have created a different output structure."
    echo "Contents of $BUILD/pyinstaller-dist/:"
    ls -la "$BUILD/pyinstaller-dist/" || true
    exit 1
fi
