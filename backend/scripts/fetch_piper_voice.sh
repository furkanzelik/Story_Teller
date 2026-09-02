#!/usr/bin/env bash
# Download a Piper voice into backend/voices/ (git-ignored, ~60MB).
# Usage: ./scripts/fetch_piper_voice.sh [nl_NL-pim-medium]
set -euo pipefail

VOICE="${1:-nl_NL-pim-medium}"          # e.g. nl_NL-pim-medium, nl_NL-mls-medium
LANG_DIR="${VOICE%%-*}"                  # nl_NL
SHORT="${VOICE#*-}"; SPK="${SHORT%%-*}"  # pim
QUAL="${VOICE##*-}"                      # medium
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/${LANG_DIR:0:2}/${LANG_DIR}/${SPK}/${QUAL}"

cd "$(dirname "$0")/../voices"
echo "Fetching $VOICE from $BASE"
curl -fSL -o "${VOICE}.onnx"      "${BASE}/${VOICE}.onnx"
curl -fSL -o "${VOICE}.onnx.json" "${BASE}/${VOICE}.onnx.json"
echo "Done: $(ls -lh "${VOICE}.onnx" | awk '{print $5}')"
