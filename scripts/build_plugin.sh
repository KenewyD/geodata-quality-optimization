#!/usr/bin/env bash
#
# Construit l'archive ZIP installable du plugin QGIS.
# Le ZIP contient un unique dossier 'geodata_quality/' comme l'exige QGIS.
#
# Usage : bash scripts/build_plugin.sh
#
set -euo pipefail

PLUGIN_DIR="geodata_quality"
DIST_DIR="dist"

# Lit la version depuis metadata.txt pour nommer l'archive.
VERSION=$(grep -E "^version=" "${PLUGIN_DIR}/metadata.txt" | cut -d'=' -f2 | tr -d '[:space:]')
ZIP_NAME="geodata_quality-${VERSION}.zip"

echo "Construction du plugin version ${VERSION}…"

rm -rf "${DIST_DIR}"
mkdir -p "${DIST_DIR}"

# On exclut les caches Python et fichiers de test du paquet distribué.
zip -r "${DIST_DIR}/${ZIP_NAME}" "${PLUGIN_DIR}" \
    -x "*/__pycache__/*" \
    -x "*.pyc" \
    -x "*/.pytest_cache/*" > /dev/null

echo "Archive créée : ${DIST_DIR}/${ZIP_NAME}"
