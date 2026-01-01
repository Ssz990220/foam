#!/usr/bin/env bash
# Full FOAM setup: build C++ binaries and pip install Python package
#
# Usage:
#   bazel run //thirdparty/foam:setup
#   # or directly:
#   ./thirdparty/foam/foam_setup.sh

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

cd "${WORKSPACE_ROOT}"

echo "=============================================="
echo "FOAM Setup"
echo "=============================================="

# Step 1: Initialize foam submodule if not present
if [[ ! -f "${FOAM_DIR}/pyproject.toml" ]]; then
    echo "Step 1: Initializing foam submodule..."
    git submodule update --init --recursive thirdparty/foam
else
    echo "Step 1: FOAM source already present"
fi

# Initialize foam's submodules (spheretree, manifold, etc.)
if [[ ! -f "${FOAM_DIR}/external/spheretree/CMakeLists.txt" ]]; then
    echo "Step 1b: Initializing foam external submodules..."
    (cd "${FOAM_DIR}" && git submodule update --init --recursive)
fi

# Step 2: Build FOAM C++ binaries with bazel
echo "Step 2: Building FOAM C++ binaries..."
bazel build //thirdparty/foam:foam

# Step 3: Copy binaries to expected location
echo "Step 3: Installing FOAM binaries..."
"${FOAM_DIR}/foam_install.sh"

# Step 4: Install FOAM Python package with uv
echo "Step 4: Installing FOAM Python package..."
if command -v uv &> /dev/null; then
    uv pip install -e "${FOAM_DIR}"
else
    echo "Warning: uv not found, trying pip..."
    pip install -e "${FOAM_DIR}"
fi

echo "=============================================="
echo "FOAM setup complete!"
echo ""
echo "You can now use FOAM sphere generation:"
echo "  uv run python -m urdf_rt_parser.main robot.urdf --gen_spheres --sphere_algo foam-medial"
echo "=============================================="
