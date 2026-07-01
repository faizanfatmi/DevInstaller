#!/usr/bin/env bash
#
# DevInstaller cross-platform setup script (Linux & macOS).
#
# Fetches the latest release, downloads the correct asset for this OS,
# verifies it (SHA256 when a checksum asset is published), installs it, and
# logs progress throughout.
#
# Configuration (environment variables, all optional):
#   DEVINSTALLER_PROVIDER   'gitlab' (default) or 'github'
#   DEVINSTALLER_GITLAB_HOST GitLab host (default: gitlab.com)
#   DEVINSTALLER_PROJECT    URL-encoded GitLab project path or numeric ID
#                           (default: faizan-fatmi-group%2Fdevinstaller)
#   DEVINSTALLER_GITHUB_REPO 'owner/repo' when PROVIDER=github
#   DEVINSTALLER_VERSION    release tag to install (default: latest)
#   DEVINSTALLER_INSTALL_DIR install prefix on Linux (default: ~/.local/bin)
#
# Usage:
#   curl -fsSL <url>/install.sh | bash
#   ./install.sh

set -euo pipefail

# ── Configuration ────────────────────────────────────────────
PROVIDER="${DEVINSTALLER_PROVIDER:-gitlab}"
GITLAB_HOST="${DEVINSTALLER_GITLAB_HOST:-gitlab.com}"
GITLAB_PROJECT="${DEVINSTALLER_PROJECT:-faizan-fatmi-group%2Fdevinstaller}"
GITHUB_REPO="${DEVINSTALLER_GITHUB_REPO:-}"
VERSION="${DEVINSTALLER_VERSION:-latest}"
INSTALL_DIR="${DEVINSTALLER_INSTALL_DIR:-$HOME/.local/bin}"

APP_NAME="DevInstaller"
LOG_PREFIX="[devinstaller]"

# ── Logging helpers ────────────────────────────────────────
if [ -t 1 ]; then
  C_RESET="\033[0m"; C_BLUE="\033[34m"; C_GREEN="\033[32m"
  C_YELLOW="\033[33m"; C_RED="\033[31m"
else
  C_RESET=""; C_BLUE=""; C_GREEN=""; C_YELLOW=""; C_RED=""
fi

info()  { printf "${C_BLUE}%s${C_RESET} %s\n"  "$LOG_PREFIX" "$*"; }
ok()    { printf "${C_GREEN}%s${C_RESET} %s\n" "$LOG_PREFIX" "$*"; }
warn()  { printf "${C_YELLOW}%s${C_RESET} %s\n" "$LOG_PREFIX" "$*" >&2; }
fail()  { printf "${C_RED}%s ERROR:${C_RESET} %s\n" "$LOG_PREFIX" "$*" >&2; exit 1; }
stage() { printf "\n${C_BLUE}==>${C_RESET} %s\n" "$*"; }

# ── Prerequisites ──────────────────────────────────────────
have() { command -v "$1" >/dev/null 2>&1; }

require_downloader() {
  if have curl; then
    DL="curl -fsSL"; DL_OUT="curl -fL -o"
  elif have wget; then
    DL="wget -qO-"; DL_OUT="wget -O"
  else
    fail "Neither curl nor wget is available. Please install one and retry."
  fi
}

fetch() { # fetch <url> -> stdout
  if have curl; then curl -fsSL "$1"; else wget -qO- "$1"; fi
}

download_to() { # download_to <url> <dest>
  info "Downloading: $1"
  if have curl; then
    curl -fL --progress-bar -o "$2" "$1" || return 1
  else
    wget -O "$2" "$1" || return 1
  fi
}

# ── OS / arch detection ─────────────────────────────────────
detect_platform() {
  local uname_s uname_m
  uname_s="$(uname -s)"
  uname_m="$(uname -m)"
  case "$uname_s" in
    Linux)  OS="linux" ;;
    Darwin) OS="macos" ;;
    *) fail "Unsupported operating system: $uname_s (use install.ps1 on Windows)." ;;
  esac
  case "$uname_m" in
    x86_64|amd64) ARCH="x86_64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *) ARCH="$uname_m" ;;
  esac
  info "Detected platform: $OS/$ARCH"
}

# ── Release resolution ──────────────────────────────────────
# Populates the ASSET_URLS array with candidate download URLs.
resolve_release() {
  ASSET_URLS=()
  if [ "$PROVIDER" = "github" ]; then
    [ -n "$GITHUB_REPO" ] || fail "DEVINSTALLER_GITHUB_REPO must be set when PROVIDER=github."
    local api
    if [ "$VERSION" = "latest" ]; then
      api="https://api.github.com/repos/${GITHUB_REPO}/releases/latest"
    else
      api="https://api.github.com/repos/${GITHUB_REPO}/releases/tags/${VERSION}"
    fi
    info "Resolving GitHub release: $api"
    local json; json="$(fetch "$api")" || fail "Could not query GitHub releases."
    # Extract browser_download_url values without requiring jq.
    while IFS= read -r url; do ASSET_URLS+=("$url"); done < <(
      printf '%s' "$json" | grep -oE '"browser_download_url":[[:space:]]*"[^"]+"' \
        | sed -E 's/.*"(https:[^"]+)"/\1/'
    )
  else
    local base="https://${GITLAB_HOST}/api/v4/projects/${GITLAB_PROJECT}/releases"
    local api
    if [ "$VERSION" = "latest" ]; then
      api="${base}/permalink/latest"
    else
      api="${base}/${VERSION}"
    fi
    info "Resolving GitLab release: $api"
    local json; json="$(fetch "$api")" || fail "Could not query GitLab releases."
    while IFS= read -r url; do ASSET_URLS+=("$url"); done < <(
      printf '%s' "$json" | grep -oE '"(direct_asset_url|url)":[[:space:]]*"[^"]+"' \
        | sed -E 's/.*"(https:[^"]+)"/\1/'
    )
  fi
  [ "${#ASSET_URLS[@]}" -gt 0 ] || fail "No downloadable assets found in the release."
}

# ── Asset selection ────────────────────────────────────────
select_asset() {
  local pattern
  if [ "$OS" = "linux" ]; then pattern='\.AppImage$'; else pattern='\.dmg$'; fi
  ASSET_URL=""
  for u in "${ASSET_URLS[@]}"; do
    if printf '%s' "$u" | grep -qiE "$pattern"; then ASSET_URL="$u"; break; fi
  done
  [ -n "$ASSET_URL" ] || fail "No asset matching $pattern found for $OS."
  # Optional checksum asset (same name + .sha256).
  CHECKSUM_URL=""
  for u in "${ASSET_URLS[@]}"; do
    case "$u" in
      "${ASSET_URL}.sha256") CHECKSUM_URL="$u"; break ;;
    esac
  done
  info "Selected asset: $ASSET_URL"
}

# ── Verification ──────────────────────────────────────────
verify_checksum() { # verify_checksum <file>
  local file="$1"
  if [ -z "$CHECKSUM_URL" ]; then
    warn "No published checksum; skipping integrity verification."
    return 0
  fi
  local expected; expected="$(fetch "$CHECKSUM_URL" | awk '{print $1}')"
  [ -n "$expected" ] || { warn "Checksum asset empty; skipping."; return 0; }
  local actual
  if have sha256sum; then actual="$(sha256sum "$file" | awk '{print $1}')";
  elif have shasum; then actual="$(shasum -a 256 "$file" | awk '{print $1}')";
  else warn "No sha256 tool found; skipping verification."; return 0; fi
  if [ "$expected" != "$actual" ]; then
    fail "Checksum mismatch! expected=$expected actual=$actual"
  fi
  ok "Checksum verified."
}

# ── Install ─────────────────────────────────────────────
install_linux() { # install_linux <file>
  mkdir -p "$INSTALL_DIR"
  local dest="$INSTALL_DIR/${APP_NAME}.AppImage"
  install -m 0755 "$1" "$dest" || cp "$1" "$dest"
  chmod +x "$dest"
  ok "Installed to $dest"
  case ":$PATH:" in
    *":$INSTALL_DIR:"*) : ;;
    *) warn "$INSTALL_DIR is not on your PATH. Add it to use '$APP_NAME' directly." ;;
  esac
}

install_macos() { # install_macos <file>
  local mnt; mnt="$(mktemp -d)"
  info "Mounting disk image…"
  hdiutil attach "$1" -nobrowse -quiet -mountpoint "$mnt" || fail "Failed to mount .dmg"
  local app; app="$(find "$mnt" -maxdepth 1 -name '*.app' -print -quit)"
  if [ -z "$app" ]; then hdiutil detach "$mnt" -quiet || true; fail "No .app found in image."; fi
  info "Copying $(basename "$app") to /Applications…"
  cp -R "$app" "/Applications/" || { hdiutil detach "$mnt" -quiet || true; fail "Copy failed (try sudo)."; }
  hdiutil detach "$mnt" -quiet || true
  ok "Installed to /Applications/$(basename "$app")"
}

# ── Main ────────────────────────────────────────────────
main() {
  stage "$APP_NAME setup"
  require_downloader
  detect_platform

  stage "Resolving latest release"
  resolve_release
  select_asset

  stage "Downloading"
  local tmp; tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  local file="$tmp/$(basename "${ASSET_URL%%\?*}")"
  download_to "$ASSET_URL" "$file" || fail "Download failed. Check your connection and retry."
  ok "Downloaded $(basename "$file")"

  stage "Verifying"
  verify_checksum "$file"

  stage "Installing"
  if [ "$OS" = "linux" ]; then install_linux "$file"; else install_macos "$file"; fi

  stage "Done"
  ok "$APP_NAME installed successfully."
}

main "$@"
