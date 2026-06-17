#!/usr/bin/env bash

if ! command -v code >/dev/null 2>&1; then
  echo "error: the 'code' CLI is not on your PATH." >&2
  echo "In VS Code: Cmd+Shift+P -> \"Shell Command: Install 'code' command in PATH\", then re-run this script." >&2
  echo "Or for a one-off run:" >&2
  echo "  export PATH=\"/Applications/Visual Studio Code.app/Contents/Resources/app/bin:\$PATH\"" >&2
  exit 1
fi

code --install-extension alexkrechik.cucumberautocomplete
code --install-extension charliermarsh.ruff
code --install-extension dbaeumer.vscode-eslint
code --install-extension deque-systems.vscode-axe-linter
code --install-extension esbenp.prettier-vscode
code --install-extension github.vscode-github-actions
code --install-extension ms-azuretools.vscode-docker
code --install-extension ms-python.isort
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-toolsai.jupyter
code --install-extension ms-toolsai.jupyter-keymap
code --install-extension ms-toolsai.jupyter-renderers
code --install-extension ms-toolsai.vscode-jupyter-cell-tags
code --install-extension ms-toolsai.vscode-jupyter-slideshow
code --install-extension ms-vscode-remote.remote-containers
code --install-extension ms-vscode.makefile-tools
code --install-extension REditorSupport.r
code --install-extension shd101wyy.markdown-preview-enhanced
code --install-extension SonarSource.sonarlint-vscode
code --install-extension tamasfe.even-better-toml
code --install-extension streetsidesoftware.code-spell-checker
code --install-extension njpwerner.autodocstring
code --install-extension vitest.explorer
code --install-extension swiftlang.swift-vscode
code --install-extension bruno-api-client.bruno