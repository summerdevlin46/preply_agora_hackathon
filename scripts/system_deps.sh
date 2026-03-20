#!/usr/bin/env bash
set -euo pipefail

OS="$(uname -s)"

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

usage() {
  cat <<EOF
Usage:
  ./scripts/system_deps.sh check
  ./scripts/system_deps.sh install
  ./scripts/system_deps.sh uninstall

Manages host system dependencies for OCR:
  - tesseract
  - poppler

macOS: uses Homebrew
Linux: uses apt-get
EOF
}

check_deps() {
  echo "Checking OCR system dependencies..."

  if have_cmd tesseract; then
    echo "✓ tesseract found at: $(command -v tesseract)"
  else
    echo "✗ tesseract not found"
  fi

  if have_cmd pdftoppm; then
    echo "✓ poppler found via pdftoppm at: $(command -v pdftoppm)"
  else
    echo "✗ poppler not found (pdftoppm missing)"
  fi
}

install_macos() {
  if ! have_cmd brew; then
    echo "Homebrew is required on macOS but was not found."
    exit 1
  fi

  if have_cmd tesseract; then
    echo "tesseract already installed"
  else
    echo "Installing tesseract..."
    brew install tesseract
  fi

  if have_cmd pdftoppm; then
    echo "poppler already installed"
  else
    echo "Installing poppler..."
    brew install poppler
  fi
}

uninstall_macos() {
  if ! have_cmd brew; then
    echo "Homebrew is required on macOS but was not found."
    exit 1
  fi

  if brew list --formula | grep -qx "tesseract"; then
    echo "Uninstalling tesseract..."
    brew uninstall tesseract
  else
    echo "tesseract is not installed via Homebrew"
  fi

  if brew list --formula | grep -qx "poppler"; then
    echo "Uninstalling poppler..."
    brew uninstall poppler
  else
    echo "poppler is not installed via Homebrew"
  fi
}

install_linux() {
  if ! have_cmd apt-get; then
    echo "This Linux install path currently supports apt-get only."
    exit 1
  fi

  sudo apt-get update

  if have_cmd tesseract; then
    echo "tesseract already installed"
  else
    echo "Installing tesseract-ocr..."
    sudo apt-get install -y tesseract-ocr
  fi

  if have_cmd pdftoppm; then
    echo "poppler already installed"
  else
    echo "Installing poppler-utils..."
    sudo apt-get install -y poppler-utils
  fi
}

uninstall_linux() {
  if ! have_cmd apt-get; then
    echo "This Linux uninstall path currently supports apt-get only."
    exit 1
  fi

  echo "Removing system OCR dependencies..."
  sudo apt-get remove -y tesseract-ocr poppler-utils || true
  sudo apt-get autoremove -y || true
}

main() {
  action="${1:-}"

  case "$action" in
    check)
      check_deps
      ;;
    install)
      if [[ "$OS" == "Darwin" ]]; then
        install_macos
      elif [[ "$OS" == "Linux" ]]; then
        install_linux
      else
        echo "Unsupported OS: $OS"
        exit 1
      fi
      ;;
    uninstall)
      if [[ "$OS" == "Darwin" ]]; then
        uninstall_macos
      elif [[ "$OS" == "Linux" ]]; then
        uninstall_linux
      else
        echo "Unsupported OS: $OS"
        exit 1
      fi
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
