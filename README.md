# DevInstaller

DevInstaller is a cross-platform desktop application that lets developers search, select, and install programming languages, compilers, SDKs, and developer tools from a comprehensive catalog — all from a single, premium Qt-based GUI.

## About

DevInstaller simplifies the setup process for developers by providing a unified interface to install tools across different operating systems. It uses native package managers (`winget`, `apt`, `brew`) and automatically handles PATH configurations, ensuring your environment is ready to use without manual tweaking.

## Features

- **Cross-Platform:** Works on Windows, Linux, and macOS using native package managers.
- **Smart Install:** Automatically skips installed tools to save time.
- **Configurable:** Easily customize the available tools by editing `tools.json`.

## Installation & Usage

### Requirements
- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)**

*Note: On Windows, it is recommended to run elevated: `uv run python -m udm --elevate`*

## Building Distributables

### Using Meson

```bash
meson setup builddir
meson compile -C builddir build-exe       # Windows .exe
meson compile -C builddir build-appimage  # Linux AppImage
meson compile -C builddir build-dmg       # macOS .dmg
```

## License

DevInstaller is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for more information.
