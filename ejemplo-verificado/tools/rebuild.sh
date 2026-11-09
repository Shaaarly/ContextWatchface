#!/bin/sh
# Full preview rebuild in one command: regenerate all art -> images/, rebuild .fprj + AOD.
# The dev server (tools/devserver.py) auto-reloads the open tab when images/ / .fprj change.
set -e
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
PY="$PROJ/venv/bin/python"
cd "$PROJ"
echo "[rebuild] render.py -> images/ (art, preview, layout.json)"
"$PY" tools/render.py . | tail -3
echo "[rebuild] build_project.py -> AnalogFull.fprj"
"$PY" tools/build_project.py | head -1
echo "[rebuild] build_aod.py -> AOD/"
"$PY" tools/build_aod.py | tail -1
echo "[rebuild] done. Preview will auto-reload at http://localhost:8777/simulator.html"
