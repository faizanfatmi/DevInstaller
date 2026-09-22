"""Translate Windows winget commands to Chocolatey (choco) commands.

When winget is missing on Windows (e.g. older Windows 10 versions, Windows Server,
or environments without the Microsoft Store), DevInstaller falls back to Chocolatey.
This module translates tool installation commands from winget to choco so that
software installations succeed without winget.
"""

from __future__ import annotations

import re

# Comprehensive tool key -> choco install command / package
WINGET_TO_CHOCO_MAP: dict[str, str] = {
    # ── Languages ──
    "python": "choco install python3 -y",
    "python311": "choco install python --version=3.11.9 -y",
    "nodejs": "choco install nodejs-lts -y",
    "typescript": "npm install -g typescript",
    "go": "choco install golang -y",
    "rust": "choco install rustup.install -y",
    "java": "choco install openjdk -y",
    "java17": "choco install openjdk17 -y",
    "csharp": "choco install dotnet-8.0-sdk -y",
    "fsharp": "choco install dotnet-8.0-sdk -y",
    "kotlin": "choco install kotlinc -y",
    "scala": "choco install scala -y",
    "groovy": "choco install groovy -y",
    "clojure": "choco install clojure -y",
    "dart": "choco install dart-sdk -y",
    "swift": "choco install swift -y",
    "ruby": "choco install ruby -y",
    "php": "choco install php -y",
    "perl": "choco install strawberryperl -y",
    "lua": "choco install lua -y",
    "luajit": "choco install luajit -y",
    "julia": "choco install julia -y",
    "r": "choco install r.project -y",
    "haskell": "choco install ghc -y",
    "ocaml": "choco install ocaml -y",
    "erlang": "choco install erlang -y",
    "elixir": "choco install elixir -y",
    "zig": "choco install zig -y",
    "nim": "choco install nim -y",
    "crystal": "choco install crystal -y",
    "vlang": "choco install vlang -y",
    "d_lang": "choco install dmd -y",
    "odin": "choco install odin -y",
    "deno": "choco install deno -y",
    "bun": "choco install bun -y",
    "solidity": "choco install solidity -y",
    "prolog": "choco install swi-prolog -y",
    "racket": "choco install racket -y",
    "scheme": "choco install mit-scheme -y",
    "common_lisp": "choco install sbcl -y",
    "pascal": "choco install freepascal -y",
    "cobol": "choco install gnucobol -y",
    "ada": "choco install gnat -y",

    # ── Compilers & Build Tools ──
    "gcc": "choco install mingw -y",
    "gpp": "choco install mingw -y",
    "clang": "choco install llvm -y",
    "mingw": "choco install mingw -y",
    "msys2": "choco install msys2 -y",
    "build_essential": "choco install make mingw -y",
    "make": "choco install make -y",
    "cmake": "choco install cmake --installargs 'ADD_CMAKE_TO_PATH=System' -y",
    "ninja": "choco install ninja -y",
    "meson": "pip install meson",
    "nasm": "choco install nasm -y",
    "yasm": "choco install yasm -y",
    "fasm": "choco install fasm -y",
    "fortran": "choco install mingw -y",
    "lldb": "choco install llvm -y",
    "gdb": "choco install mingw -y",
    "wasm": "choco install emscripten -y",
    "wasmtime": "choco install wasmtime -y",

    # ── Package Managers ──
    "pip": "python -m ensurepip --upgrade",
    "maven": "choco install maven -y",
    "gradle": "choco install gradle -y",
    "npm": "choco install nodejs-lts -y",
    "yarn": "choco install yarn -y",
    "pnpm": "choco install pnpm -y",
    "cargo": "choco install rustup.install -y",
    "gem": "choco install ruby -y",
    "composer": "choco install composer -y",
    "rustup": "choco install rustup.install -y",
    "vcpkg": "choco install vcpkg -y",
    "conan": "pip install conan",
    "pipenv": "pip install pipenv",
    "poetry": "pip install poetry",
    "uv": "powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"",
    "homebrew": "",
    "scoop": "powershell -c \"Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser; iex (new-object net.webclient).downloadstring('https://get.scoop.sh')\"",
    "chocolatey": "powershell -c \"Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))\"",

    # ── Databases ──
    "mysql": "choco install mysql -y",
    "postgres": "choco install postgresql -y",
    "mongodb": "choco install mongodb -y",
    "redis": "choco install redis-64 -y",
    "sqlite": "choco install sqlite -y",

    # ── DevOps & Tools ──
    "git": "choco install git -y",
    "gh_cli": "choco install gh -y",
    "docker": "choco install docker-desktop -y",
    "podman": "choco install podman-desktop -y",
    "kubernetes": "choco install kubernetes-cli -y",
    "helm": "choco install kubernetes-helm -y",
    "terraform": "choco install terraform -y",
    "ansible": "pip install ansible",
    "vagrant": "choco install vagrant -y",
    "postman": "choco install postman -y",
    "insomnia": "choco install insomnia-rest-api-client -y",
    "ngrok": "choco install ngrok -y",
    "protobuf": "choco install protoc -y",
    "grpcurl": "choco install grpcurl -y",
    "wsl": "wsl --install",
    "powershell7": "choco install powershell-core -y",
    "windows_terminal": "choco install microsoft-windows-terminal -y",
    "curl": "choco install curl -y",
    "wget": "choco install wget -y",
    "jq": "choco install jq -y",
    "ffmpeg": "choco install ffmpeg -y",
    "imagemagick": "choco install imagemagick -y",
    "7zip": "choco install 7zip -y",
    "lazygit": "choco install lazygit -y",
    "ripgrep": "choco install ripgrep -y",
    "fd": "choco install fd -y",
    "bat": "choco install bat -y",
    "fzf": "choco install fzf -y",
    "valgrind": "",

    # ── IDEs & Editors ──
    "vscode": "choco install vscode -y",
    "sublime": "choco install sublimetext4 -y",
    "neovim": "choco install neovim -y",
    "intellij": "choco install intellijidea-community -y",

    # ── SDKs & Frameworks ──
    "dotnet": "choco install dotnet-8.0-sdk -y",

    # ── Mobile Development ──
    "flutter": "choco install flutter -y",
    "android_sdk": "choco install androidstudio -y",
    "react_native": "npm install -g react-native-cli",

    # ── Cloud CLIs ──
    "aws_cli": "choco install awscli -y",
    "gcloud": "choco install gcloudsdk -y",
    "azure_cli": "choco install azure-cli -y",

    # ── AI / Data Science ──
    "tensorflow": "pip install tensorflow",
    "pytorch": "pip install torch torchvision torchaudio",
    "cuda": "choco install cuda -y",
    "anaconda": "choco install anaconda3 -y",
    "miniconda": "choco install miniconda3 -y",
    "jupyter": "pip install notebook jupyterlab",
}


def translate_winget_to_choco(cmd: str, tool: dict | None = None) -> str:
    """Translate a winget command into an equivalent Chocolatey or native command.

    If a tool dict is provided, we first check the curated WINGET_TO_CHOCO_MAP.
    Otherwise, we parse the winget ID or tool name and emit a `choco install <pkg> -y`.
    """
    if not cmd or "winget" not in cmd:
        return cmd

    key = tool.get("key", "").lower() if tool else ""
    if key and key in WINGET_TO_CHOCO_MAP and WINGET_TO_CHOCO_MAP[key]:
        return WINGET_TO_CHOCO_MAP[key]

    # Try extracting winget package ID from command, e.g. `--id Kitware.CMake`
    match = re.search(r"--id\s+([\w\.\-]+)", cmd)
    if match:
        raw_id = match.group(1)
        # Take the trailing part of the ID, e.g. Kitware.CMake -> cmake
        pkg_part = raw_id.split(".")[-1].lower()
        return f"choco install {pkg_part} -y"

    if key:
        return f"choco install {key} -y"

    return cmd
