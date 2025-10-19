#!/usr/bin/env bash

# Installs the speech-to-cli dashboard launcher to the current user's desktop menu.
# Copies/links the dashboard entry to ~/.local/bin and registers a .desktop file
# that points to that command.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASHBOARD_SCRIPT="$ROOT_DIR/scripts/dashboard.py"
ICON_SOURCE="$ROOT_DIR/assets/speech-to-cli-dashboard.svg"

if [[ ! -x "$DASHBOARD_SCRIPT" ]]; then
  echo "Feil: $DASHBOARD_SCRIPT er ikke kjørbar." >&2
  echo "Kjør 'chmod +x $DASHBOARD_SCRIPT' og prøv igjen." >&2
  exit 1
fi

if ! python3 - <<'PY' >/dev/null 2>&1
import tkinter  # noqa: F401
PY
then
  if command -v apt-get >/dev/null 2>&1; then
    echo "Installerer avhengighet: python3-tk (kreves for GUI)..."
    if ! sudo apt-get update >/dev/null 2>&1; then
      echo "Advarsel: kunne ikke oppdatere apt-cache. Fortsetter." >&2
    fi
    if ! sudo apt-get install -y python3-tk; then
      echo "Feil: installasjon av python3-tk feilet. Installer pakken manuelt og prøv igjen." >&2
      exit 1
    fi
  else
    echo "Feil: Tkinter mangler, og apt-get ble ikke funnet. Installer python3-tk manuelt og prøv igjen." >&2
    exit 1
  fi
fi

LOCAL_BIN="${HOME}/.local/bin"
LOCAL_APPS="${HOME}/.local/share/applications"
LOCAL_ICONS="${HOME}/.local/share/icons/hicolor/scalable/apps"

mkdir -p "$LOCAL_BIN" "$LOCAL_APPS"
if [[ -f "$ICON_SOURCE" ]]; then
  mkdir -p "$LOCAL_ICONS"
  cp "$ICON_SOURCE" "$LOCAL_ICONS/speech-to-cli-dashboard.svg"
fi

TARGET_BIN="${LOCAL_BIN}/speech-to-cli-dashboard"
TARGET_DESKTOP="${LOCAL_APPS}/speech-to-cli-dashboard.desktop"

ln -sf "$DASHBOARD_SCRIPT" "$TARGET_BIN"
chmod +x "$TARGET_BIN"

cat >"$TARGET_DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=Speech-to-CLI Dashboard
Comment=Start or stop the speech-to-cli daemon
Exec=speech-to-cli-dashboard
Icon=speech-to-cli-dashboard
Terminal=false
Categories=Utility;
EOF

chmod +x "$TARGET_DESKTOP"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$LOCAL_APPS" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "${HOME}/.local/share/icons" >/dev/null 2>&1 || true
fi

echo "Dashboard installert:"
echo "  Kommandonavn : speech-to-cli-dashboard"
echo "  Desktopfil   : $TARGET_DESKTOP"
