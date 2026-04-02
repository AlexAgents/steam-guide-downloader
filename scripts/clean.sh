# Cleanup script for Linux / macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo ""
echo "═══════════════════════════════════════════"
echo "  Steam Guide Downloader — Cleanup"
echo "═══════════════════════════════════════════"
echo ""

cd "$ROOT"

for d in build dist; do
    if [ -d "$d" ]; then
        rm -rf "$d"
        echo "  Removed: $d/"
    fi
done

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "  Removed: __pycache__ dirs"

find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
echo "  Removed: .pytest_cache dirs"

find . -maxdepth 1 -name "*.spec" -delete 2>/dev/null || true
echo "  Removed: *.spec files"

find assets -name "chk_*.png" -delete 2>/dev/null || true
echo "  Removed: generated checkbox PNGs"

echo ""
echo "  Cleanup complete."
echo "═══════════════════════════════════════════"
echo ""