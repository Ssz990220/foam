#!/usr/bin/env bash
# Install FOAM binaries to the expected location for the Python module
#
# This script copies the bazel-built FOAM binaries to foam/external/
# so the Python module can find them.
#
# Usage:
#   bazel run //thirdparty/foam:install

set -euo pipefail

# Find paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Handle running from bazel runfiles
if [[ -n "${BUILD_WORKSPACE_DIRECTORY:-}" ]]; then
    WORKSPACE_ROOT="${BUILD_WORKSPACE_DIRECTORY}"
    FOAM_DIR="${WORKSPACE_ROOT}/thirdparty/foam"
else
    # Running directly from foam directory
    FOAM_DIR="${SCRIPT_DIR}"
    WORKSPACE_ROOT="${FOAM_DIR}/../.."
fi

FOAM_BIN_SRC="${WORKSPACE_ROOT}/bazel-bin/thirdparty/foam/foam/bin"
FOAM_BIN_DST="${FOAM_DIR}/foam/external"

echo "Installing FOAM binaries..."
echo "  Source: ${FOAM_BIN_SRC}"
echo "  Destination: ${FOAM_BIN_DST}"

# Check if source exists
if [[ ! -d "${FOAM_BIN_SRC}" ]]; then
    echo "Error: FOAM binaries not found at ${FOAM_BIN_SRC}"
    echo "Please run 'bazel build //thirdparty/foam:foam' first"
    exit 1
fi

# Create destination directory if needed
mkdir -p "${FOAM_BIN_DST}"

# Copy binaries
BINARIES=(
    "makeTreeGrid"
    "makeTreeHubbard"
    "makeTreeMedial"
    "makeTreeOctree"
    "makeTreeSpawn"
    "manifold"
    "manifold_old"
    "simplify"
    "simplify_old"
)

for binary in "${BINARIES[@]}"; do
    if [[ -f "${FOAM_BIN_SRC}/${binary}" ]]; then
        cp -v "${FOAM_BIN_SRC}/${binary}" "${FOAM_BIN_DST}/"
        chmod +x "${FOAM_BIN_DST}/${binary}"
    else
        echo "Warning: ${binary} not found in ${FOAM_BIN_SRC}"
    fi
done

echo "FOAM binaries installed successfully!"
