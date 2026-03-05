#!/bin/bash
# Build React dashboard and copy to static/dash/
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/_features/frontend-code/youtube-9d-dash"
OUTPUT_DIR="$PROJECT_ROOT/static/dash"

echo "Building React dashboard..."
cd "$FRONTEND_DIR"
npm run build

echo "Copying build to $OUTPUT_DIR..."
rm -rf "$OUTPUT_DIR"
cp -r dist "$OUTPUT_DIR"

echo "Done! Dashboard built and copied to static/dash/"
ls -la "$OUTPUT_DIR"
