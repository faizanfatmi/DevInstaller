"""Centralized icon and visual asset provider for DevInstaller tools."""

from pathlib import Path
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap
)

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

TOOL_ICONS_MAP = {
    # ── Languages (100% real official icons) ──
    "python": "python.png",
    "python311": "python.png",
    "nodejs": "node.png",
    "node": "node.png",
    "typescript": "typescript.png",
    "ts": "typescript.png",
    "javascript": "javascript.png",
    "js": "javascript.png",
    "go": "go.png",
    "golang": "go.png",
    "rust": "rust.png",
    "java": "java.png",
    "java17": "java.png",
    "java21": "java.png",
    "csharp": "csharp.png",
    "dotnet": "csharp.png",
    "fsharp": "csharp.png",
    "kotlin": "kotlin.png",
    "scala": "scala.png",
    "groovy": "groovy.png",
    "clojure": "clojure.png",
    "dart": "dart.png",
    "swift": "swift.png",
    "ruby": "ruby.png",
    "php": "php.png",
    "perl": "perl.png",
    "lua": "lua.png",
    "luajit": "lua.png",
    "julia": "julia.png",
    "r": "r.png",
    "haskell": "haskell.png",
    "ocaml": "ocaml.png",
    "erlang": "erlang.png",
    "elixir": "elixir.png",
    "zig": "zig.png",
    "nim": "nim.png",
    "crystal": "crystal.png",
    "vlang": "vlang.png",
    "d_lang": "dlang.png",
    "dlang": "dlang.png",
    "odin": "odin.png",
    "deno": "deno.png",
    "bun": "bun.png",
    "solidity": "solidity.png",
    "prolog": "prolog.png",
    "racket": "racket.png",
    "scheme": "scheme.png",
    "common_lisp": "common_lisp.png",
    "pascal": "gcc.png",
    "cobol": "gcc.png",
    "ada": "gcc.png",

    # ── Compilers & Build Tools ──
    "gcc": "gcc.png",
    "gpp": "cpp.png",
    "cpp": "cpp.png",
    "c": "c.png",
    "clang": "clang.png",
    "llvm": "clang.png",
    "lldb": "clang.png",
    "mingw": "gcc.png",
    "msys2": "gcc.png",
    "build_essential": "gcc.png",
    "make": "gcc.png",
    "cmake": "cmake.png",
    "ninja": "cpp.png",
    "fortran": "gcc.png",
    "gdb": "gcc.png",

    # ── Package Managers ──
    "pip": "pip.png",
    "npm": "npm.png",
    "yarn": "yarn.png",
    "pnpm": "npm.png",
    "cargo": "rust.png",
    "rustup": "rust.png",
    "gem": "ruby.png",
    "composer": "composer.png",
    "maven": "java.png",
    "gradle": "java.png",

    # ── Databases ──
    "postgres": "postgres.png",
    "postgresql": "postgres.png",
    "mysql": "mysql.png",
    "redis": "redis.png",
    "mongodb": "mongodb.png",
    "sqlite": "sqlite.png",

    # ── DevOps & Tools ──
    "docker": "docker.png",
    "podman": "docker.png",
    "git": "git.png",
    "gh_cli": "git.png",
    "kubernetes": "kubernetes.png",
    "helm": "helm.png",
    "terraform": "terraform.png",
    "ansible": "ansible.png",
    "vagrant": "vagrant.png",
    "postman": "postman.png",
    "insomnia": "postman.png",
    "powershell7": "powershell.png",
    "windows_terminal": "powershell.png",

    # ── IDEs & Editors ──
    "vscode": "vscode.png",
    "sublime": "sublime.png",
    "neovim": "neovim.png",
    "intellij": "intellij.png",

    # ── Mobile & Web ──
    "flutter": "flutter.png",
    "android_sdk": "android.png",
    "react_native": "javascript.png",
}

CATEGORY_COLORS = {
    "Languages": ("#818cf8", "rgba(99, 102, 241, 0.22)"),
    "Package Managers": ("#fb923c", "rgba(234, 88, 12, 0.20)"),
    "Compilers": ("#34d399", "rgba(16, 185, 129, 0.20)"),
    "Databases": ("#22d3ee", "rgba(34, 211, 238, 0.20)"),
    "DevOps Tools": ("#38bdf8", "rgba(56, 189, 248, 0.20)"),
    "DevOps & Tools": ("#38bdf8", "rgba(56, 189, 248, 0.20)"),
    "IDEs & Editors": ("#34d399", "rgba(52, 211, 153, 0.20)"),
    "Cloud CLIs": ("#93c5fd", "rgba(147, 197, 253, 0.20)"),
    "Mobile Development": ("#f87171", "rgba(248, 113, 113, 0.20)"),
    "Data Science": ("#f472b6", "rgba(244, 114, 182, 0.20)"),
    "AI / Data Science": ("#f472b6", "rgba(244, 114, 182, 0.20)"),
    "SDKs & Frameworks": ("#c084fc", "rgba(192, 132, 252, 0.20)"),
}

_PIXMAP_CACHE = {}

def get_tool_icon_pixmap(tool: dict, size: int = 36) -> QPixmap:
    """Return a crisp, high-resolution QPixmap icon for any tool."""
    key = tool.get("key", "").lower()
    cache_key = f"{key}_{size}"
    if cache_key in _PIXMAP_CACHE:
        return _PIXMAP_CACHE[cache_key]

    # 1. Check for authentic PNG asset
    fname = TOOL_ICONS_MAP.get(key)
    if fname:
        p = ICONS_DIR / fname
        if p.exists():
            pix = QPixmap(str(p))
            if not pix.isNull():
                scaled = pix.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                _PIXMAP_CACHE[cache_key] = scaled
                return scaled

    # 2. Dynamic high-DPI monogram badge in category accent color
    name = tool.get("name", key)
    cat = tool.get("category", "Other")
    fg_hex, _ = CATEGORY_COLORS.get(cat, ("#94a3b8", "rgba(255, 255, 255, 0.08)"))

    res = max(size * 2, 72)
    img = QImage(res, res, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(0)

    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    bg_path = QPainterPath()
    bg_path.addRoundedRect(QRectF(3, 3, res - 6, res - 6), 16, 16)
    c = QColor(fg_hex)
    painter.fillPath(bg_path, QColor(c.red(), c.green(), c.blue(), 50))
    painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 140), 2.5))
    painter.drawPath(bg_path)

    clean_name = name.replace("(", " ").replace(")", " ").replace("-", " ").replace("_", " ")
    words = clean_name.split()
    if len(words) >= 2:
        initials = (words[0][0] + words[1][0]).upper()
    elif words:
        initials = words[0][:2].upper()
    else:
        initials = key[:2].upper()

    painter.setPen(QColor(fg_hex))
    font = QFont("Segoe UI", int(res * 0.38))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(QRectF(0, 0, res, res - 2), Qt.AlignmentFlag.AlignCenter, initials)
    painter.end()

    scaled = QPixmap.fromImage(img).scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    _PIXMAP_CACHE[cache_key] = scaled
    return scaled
