#!/usr/bin/env bash

if ! command -v code >/dev/null 2>&1; then
  echo "error: the 'code' CLI is not on your PATH." >&2
  echo "In VS Code: Cmd+Shift+P -> \"Shell Command: Install 'code' command in PATH\", then re-run this script." >&2
  echo "Or for a one-off run:" >&2
  echo "  export PATH=\"/Applications/Visual Studio Code.app/Contents/Resources/app/bin:\$PATH\"" >&2
  exit 1
fi

# Recommended extensions are listed in .vscode/extensions.json
EXTENSIONS_JSON="$(dirname "$0")/../.vscode/extensions.json"
grep -o '"[A-Za-z0-9-]*\.[A-Za-z0-9.-]*"' "$EXTENSIONS_JSON" | tr -d '"' | xargs -n1 code --install-extension

# Optional extensions for specific parts of the repo (mobile, R, notebooks, etc.)
code --install-extension alexkrechik.cucumberautocomplete
code --install-extension bruno-api-client.bruno
code --install-extension deque-systems.vscode-axe-linter
code --install-extension esbenp.prettier-vscode
code --install-extension ms-toolsai.jupyter
code --install-extension ms-toolsai.jupyter-keymap
code --install-extension ms-toolsai.jupyter-renderers
code --install-extension ms-toolsai.vscode-jupyter-cell-tags
code --install-extension ms-toolsai.vscode-jupyter-slideshow
code --install-extension ms-vscode-remote.remote-containers
code --install-extension ms-vscode.makefile-tools
code --install-extension REditorSupport.r
code --install-extension shd101wyy.markdown-preview-enhanced
code --install-extension swiftlang.swift-vscode
