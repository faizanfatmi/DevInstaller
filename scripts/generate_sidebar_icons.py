"""Generate modern monochrome line outline icons for DevInstaller sidebar and full UI matching DevForge Dark design."""

from pathlib import Path
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication
import sys

app = QApplication.instance() or QApplication(sys.argv)
from PySide6.QtSvg import QSvgRenderer

ICONS_DIR = Path(__file__).resolve().parent.parent / "src" / "udm" / "assets" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

STROKE = "#becab9"

def make_svg(inner_content: str, stroke: str = STROKE, stroke_width: str = "1.8") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
{inner_content}
</svg>'''

ICONS = {
    # ── Sidebar Icons ──
    # 1. All Packages - Archive Storage Box with Lid and Front Handle Slot
    "sb_all": make_svg(f'''  <rect x="2.5" y="4" width="19" height="4.5" rx="1.2" />
  <path d="M4 8.5v9.5a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8.5" />
  <rect x="9" y="12" width="6" height="2.5" rx="0.8" stroke-width="1.5" />'''),

    # 2. AI / Data Science - Profile head facing left with mechanical cog/gear inside cranium
    "sb_data_science": make_svg(f'''  <path d="M16 21v-3c0-1.2.6-2.2 1.4-3 1-1 1.6-2.3 1.6-3.8 0-4-3-7-7-7-2.6 0-4.8 1.4-5.9 3.5L4 10l1.8 1.4v1.8c0 1.2.8 2.4 1.8 3l.4 2.8" />
  <path d="M8 21v-2" />
  <circle cx="13" cy="9.5" r="2.5" />
  <circle cx="13" cy="9.5" r="1.1" fill="{STROKE}" />
  <line x1="13" y1="6" x2="13" y2="7" />
  <line x1="13" y1="12" x2="13" y2="13" />
  <line x1="9.5" y1="9.5" x2="10.5" y2="9.5" />
  <line x1="15.5" y1="9.5" x2="16.5" y2="9.5" />
  <line x1="10.5" y1="7" x2="11.2" y2="7.7" />
  <line x1="14.8" y1="11.3" x2="15.5" y2="12" />
  <line x1="10.5" y1="12" x2="11.2" y2="11.3" />
  <line x1="14.8" y1="7.7" x2="15.5" y2="7" />'''),

    # 3. Cloud CLIs - Cloud outline
    "sb_cloud": make_svg('''  <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />'''),

    # 4. Compilers - Circle with combination wrench (open jaw top-left, ring bottom-right)
    "sb_compilers": make_svg(f'''  <circle cx="12" cy="12" r="9.5" />
  <line x1="9" y1="9.5" x2="13.8" y2="14.3" stroke-width="2" />
  <path d="M10.8 6.5a2.2 2.2 0 0 0-2.8.2L6.8 8a2.2 2.2 0 0 0 .2 3.1l1-1a1 1 0 0 1 0-1.4l.7-.7a1 1 0 0 1 1.4 0l.7.7Z" stroke-width="1.5" />
  <circle cx="15" cy="15.5" r="2.2" stroke-width="1.6" />
  <circle cx="15" cy="15.5" r="0.9" fill="{STROKE}" />'''),

    # 5. Databases - Stacked cylindrical database disks (3 tiers)
    "sb_databases": make_svg('''  <ellipse cx="12" cy="5" rx="8" ry="2.6" />
  <path d="M4 5v4.5c0 1.4 3.6 2.6 8 2.6s8-1.2 8-2.6V5" />
  <path d="M4 9.5V14c0 1.4 3.6 2.6 8 2.6s8-1.2 8-2.6V9.5" />
  <path d="M4 14v4.5c0 1.4 3.6 2.6 8 2.6s8-1.2 8-2.6V14" />'''),

    # 6. DevOps Tools - Git branch / fork splitting with arrows
    "sb_devops": make_svg('''  <line x1="12" y1="21" x2="12" y2="13" stroke-width="2" />
  <path d="M12 13c0-3-3-5.5-6-7" stroke-width="2" />
  <polyline points="4.5 9.5 5.5 5.5 9.5 6.5" stroke-width="1.8" />
  <path d="M12 13c0-3 3-5.5 6-7" stroke-width="2" />
  <polyline points="14.5 6.5 18.5 5.5 19.5 9.5" stroke-width="1.8" />
  <circle cx="12" cy="20.5" r="1.2" fill="#becab9" />'''),

    # 7. IDEs & Editors - Rounded code square with < >
    "sb_ides": make_svg('''  <rect x="3" y="3" width="18" height="18" rx="4" />
  <polyline points="9.5 8.5 6.5 12 9.5 15.5" stroke-width="2" />
  <polyline points="14.5 8.5 17.5 12 14.5 15.5" stroke-width="2" />'''),

    # 8. Languages - Terminal window with >_
    "sb_languages": make_svg('''  <rect x="3" y="4" width="18" height="16" rx="3" />
  <polyline points="7 9 10 12 7 15" stroke-width="2" />
  <line x1="12.5" y1="15" x2="16.5" y2="15" stroke-width="2" />'''),

    # 9. Mobile Dev - Tablet on left, smartphone in foreground on right
    "sb_mobile": make_svg('''  <rect x="2" y="5" width="13" height="14" rx="2" />
  <line x1="6" y1="16.5" x2="9" y2="16.5" stroke-width="1.8" />
  <rect x="12" y="7" width="9" height="14" rx="2" fill="#101319" stroke="#becab9" stroke-width="1.8" />
  <line x1="15" y1="18.5" x2="18" y2="18.5" stroke-width="1.8" />
  <circle cx="16.5" cy="9.5" r="0.6" fill="#becab9" />'''),

    # 10. Package Managers - Isometric 3D package cube
    "sb_packages": make_svg('''  <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3z" />
  <path d="M12 12 4 7.5" />
  <path d="m12 12 8-4.5" />
  <path d="M12 12v9" />
  <path d="m7.5 5.5 8 4.5" stroke-width="1.4" />'''),

    # 11. SDKs & Frameworks - Stacked layers outline
    "sb_sdks": make_svg('''  <path d="m12 2 9 5-9 5-9-5 9-5z" />
  <path d="m3 12 9 5 9-5" />
  <path d="m3 17 9 5 9-5" />'''),

    # ── Full UI Matching Icons (Replacing Emojis) ──
    # Search icon
    "icon_search": make_svg('''  <circle cx="11" cy="11" r="7.5" />
  <line x1="16.5" y1="16.5" x2="21" y2="21" stroke-width="2.2" />'''),

    # Download / Install icon (primary emerald button)
    "icon_download": make_svg('''  <path d="M12 3v13m0 0-4-4m4 4 4-4" stroke-width="2.2" />
  <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" stroke-width="2" />''', stroke="#00390e"),

    # Download icon in muted silver
    "icon_download_silver": make_svg('''  <path d="M12 3v13m0 0-4-4m4 4 4-4" stroke-width="2.2" />
  <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" stroke-width="2" />''', stroke="#becab9"),

    # Reinstall / Refresh icon
    "icon_refresh": make_svg('''  <path d="M21 12a9 9 0 0 0-9-9 9.7 9.7 0 0 0-6.7 2.7L3 8" stroke-width="2" />
  <polyline points="3 3 3 8 8 8" stroke-width="2" />
  <path d="M3 12a9 9 0 0 0 9 9 9.7 9.7 0 0 0 6.7-2.7L21 16" stroke-width="2" />
  <polyline points="16 16 21 16 21 21" stroke-width="2" />''', stroke="#00390e"),

    # Trash / Uninstall icon (danger red / coral)
    "icon_trash": make_svg('''  <line x1="3" y1="6" x2="21" y2="6" stroke-width="2" />
  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke-width="1.8" />
  <line x1="10" y1="11" x2="10" y2="17" />
  <line x1="14" y1="11" x2="14" y2="17" />''', stroke="#ffb4ab"),

    # Trash icon in muted silver (for Log clear button)
    "icon_trash_silver": make_svg('''  <line x1="3" y1="6" x2="21" y2="6" stroke-width="2" />
  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke-width="1.8" />
  <line x1="10" y1="11" x2="10" y2="17" />
  <line x1="14" y1="11" x2="14" y2="17" />''', stroke="#becab9"),

    # Meta Package Name (cube outline)
    "meta_pkg": make_svg('''  <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3z" />
  <path d="M12 12 4 7.5" />
  <path d="m12 12 8-4.5" />
  <path d="M12 12v9" />'''),

    # Meta Version / Settings (gear outline)
    "meta_gear": make_svg('''  <circle cx="12" cy="12" r="3.2" />
  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />'''),

    # Meta Category (tag outline)
    "meta_tag": make_svg('''  <path d="m20.5 13.5-7 7a2 2 0 0 1-2.8 0L2 12V3h9l9.5 9.5a2 2 0 0 1 0 2.8z" />
  <circle cx="7" cy="7" r="1.5" fill="#becab9" />'''),

    # Meta Size (disk / hard drive outline)
    "meta_disk": make_svg('''  <rect x="2" y="5" width="20" height="14" rx="2" />
  <line x1="2" y1="13" x2="22" y2="13" />
  <circle cx="18" cy="16.5" r="1" fill="#becab9" />
  <line x1="6" y1="9" x2="10" y2="9" />'''),

    # Meta Docs / Logs (document outline)
    "meta_doc": make_svg('''  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
  <polyline points="14 2 14 8 20 8" />
  <line x1="16" y1="13" x2="8" y2="13" />
  <line x1="16" y1="17" x2="8" y2="17" />
  <line x1="10" y1="9" x2="8" y2="9" />'''),

    # Link Globe (official website)
    "link_globe": make_svg('''  <circle cx="12" cy="12" r="10" />
  <line x1="2" y1="12" x2="22" y2="12" />
  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />'''),

    # Link Book (documentation)
    "link_book": make_svg('''  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />'''),

    # Link Code (source code)
    "link_code": make_svg('''  <polyline points="16 18 22 12 16 6" />
  <polyline points="8 6 2 12 8 18" />'''),

    # OS Windows
    "os_windows": make_svg('''  <rect x="3" y="3" width="8" height="8" rx="1" />
  <rect x="13" y="3" width="8" height="8" rx="1" />
  <rect x="3" y="13" width="8" height="8" rx="1" />
  <rect x="13" y="13" width="8" height="8" rx="1" />'''),

    # OS macOS (Apple outline)
    "os_mac": make_svg('''  <path d="M12 2c.5 1.5-.5 3-1.5 3.5-.8-.8-1-2-.5-3.5 1 0 1.5 0 2 0z" />
  <path d="M18.7 17.5c-.7 1.6-1.7 3.2-3.1 3.2-1.3 0-1.8-.8-3.4-.8-1.6 0-2.2.8-3.4.8-1.4 0-2.6-1.8-3.4-3.5C4 14.5 4 10.5 5.7 9c1.4-1.2 3.1-1.3 4.2-.5 1 .6 1.7.9 2.4.9.7 0 1.5-.4 2.5-.9 1.5-.8 3.2-.6 4.3.6-2.5 1.5-2.1 4.7.6 5.9-.3.9-.6 1.7-1 2.5z" />'''),

    # OS Linux (Terminal prompt)
    "os_linux": make_svg('''  <rect x="3" y="4" width="18" height="16" rx="3" />
  <polyline points="7 9 10 12 7 15" stroke-width="2" />
  <line x1="12.5" y1="15" x2="16.5" y2="15" stroke-width="2" />'''),
}

def render_all():
    size = 64
    for name, svg_content in ICONS.items():
        # Save SVG
        svg_file = ICONS_DIR / f"{name}.svg"
        svg_file.write_text(svg_content, encoding="utf-8")

        # Render to PNG
        renderer = QSvgRenderer(QByteArray(svg_content.encode("utf-8")))
        img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(0, 0, 0, 0))
        painter = QPainter(img)
        renderer.render(painter)
        painter.end()

        png_file = ICONS_DIR / f"{name}.png"
        img.save(str(png_file))
        print(f"Rendered {png_file.name} (64x64)")

if __name__ == "__main__":
    render_all()
