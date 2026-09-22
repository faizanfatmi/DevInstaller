"""Build Windows .exe using PyInstaller."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def main():
    print("Syncing versions from meson.build...")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "sync_version.py")], check=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        "UniversalDevManager",
        "--icon",
        str(ROOT / "logo.ico"),
        "--add-data",
        f"{ROOT / 'logo.png'}{';' if sys.platform == 'win32' else ':'}.",
        "--add-data",
        f"{ROOT / 'tools.json'}{';' if sys.platform == 'win32' else ':'}.",
        "--add-data",
        f"{ROOT / 'src' / 'udm' / 'assets'}{';' if sys.platform == 'win32' else ':'}src/udm/assets",
        "--hidden-import",
        "PySide6.QtCore",
        "--hidden-import",
        "PySide6.QtGui",
        "--hidden-import",
        "PySide6.QtWidgets",
        "--distpath",
        str(DIST),
        "--workpath",
        str(ROOT / "build" / "pyinstaller"),
        "--specpath",
        str(ROOT / "build"),
        str(ROOT / "main.py"),
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
