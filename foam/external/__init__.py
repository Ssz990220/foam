from sys import stdout
from pathlib import Path
from os import remove as remove_file, environ
from subprocess import run, DEVNULL

from trimesh.exchange.obj import export_obj
from trimesh.base import Trimesh

from foam.model import *
from foam.utility import export_obj_with_normals, tempmesh, load_mesh_file


def _find_binary(name: str) -> Path:
    """Find a binary in multiple possible locations.

    Search order:
    1. FOAM_BIN_DIR environment variable
    2. Bazel runfiles (if running under bazel)
    3. Local foam/external directory
    4. Bazel output directory relative to workspace root
    """
    # Check environment variable first
    if "FOAM_BIN_DIR" in environ:
        path = Path(environ["FOAM_BIN_DIR"]) / name
        if path.exists():
            return path

    # Check local directory (cmake build output)
    local_dir = Path(__file__).parent
    local_path = local_dir / name
    if local_path.exists():
        return local_path

    # Check bazel-bin relative to workspace root
    # Walk up from this file to find workspace root (contains MODULE.bazel or WORKSPACE)
    current = local_dir
    for _ in range(10):  # Limit search depth
        bazel_bin = current / "bazel-bin" / "thirdparty" / "foam" / "foam" / "bin" / name
        if bazel_bin.exists():
            return bazel_bin
        # Also check if we're at workspace root
        if (current / "MODULE.bazel").exists() or (current / "WORKSPACE").exists():
            bazel_bin = current / "bazel-bin" / "thirdparty" / "foam" / "foam" / "bin" / name
            if bazel_bin.exists():
                return bazel_bin
            break
        current = current.parent

    # Check bazel runfiles (when running as bazel target)
    runfiles_dir = environ.get("RUNFILES_DIR", "")
    if runfiles_dir:
        runfiles_path = Path(runfiles_dir) / "foam" / "bin" / name
        if runfiles_path.exists():
            return runfiles_path

    # Fallback to local path (will fail with clear error if not found)
    return local_path


EXTERNAL_BINARY_DIR = Path(__file__).parent
MAKE_TREE_MEDIAL_PATH = _find_binary("makeTreeMedial")
MAKE_TREE_GRID_PATH = _find_binary("makeTreeGrid")
MAKE_TREE_HUBBARD_PATH = _find_binary("makeTreeHubbard")
MAKE_TREE_OCTREE_PATH = _find_binary("makeTreeOctree")
MAKE_TREE_SPAWN_PATH = _find_binary("makeTreeSpawn")
MANIFOLD_PATH = _find_binary("manifold")
SIMPLIFY_PATH = _find_binary("simplify")
MANIFOLD_OLD_PATH = _find_binary("manifold_old")
SIMPLIFY_OLD_PATH = _find_binary("simplify_old")


def read_spherization_file(filename: Path, offset: NDArray) -> list[Spherization]:
    output = []
    with open(filename, 'r') as output_spheres:
        lines = output_spheres.readlines()
        spheres_per_level = [int(line.split(':')[1]) for line in lines if 'Num' in line]
        best_error = [float(line.split(':')[1]) for line in lines if 'Best' in line]
        worst_error = [float(line.split(':')[1]) for line in lines if 'Worst' in line]
        mean_error = [float(line.split(':')[1]) for line in lines if 'Mean' in line]

        for i, (level, mean, best, worst) in enumerate(zip(spheres_per_level,
                                                           mean_error,
                                                           best_error,
                                                           worst_error,
                                                           strict = True)):
            start = 1 + sum(spheres_per_level[:i])
            spheres = [
                Sphere(*list(map(float, line.split()))[:-1], offset) # type: ignore
                for line in lines[start:start + level]
                ]

            spheres = list(filter(lambda s: s.radius > 0, spheres))
            output.append(Spherization(spheres, mean, best, worst))

    return output


def compute_spheres_helper(mesh: Trimesh, command: list[str],method) -> list[Spherization]:
    # print(command)
    # print("flag 5")
    _ = mesh.vertex_normals    # Need to compute vertex normals
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj_with_normals(mesh))
        input_mesh.flush()

        output_file = input_path.parent / (input_path.stem + f'-{method}.sph')
        # print(command)
        sphere_output = run(command + [str(input_path)], capture_output=True)

    if sphere_output.returncode != 0:
        raise RuntimeError(f"Failed to create spheres for mesh. Mesh is probably invalid. {sphere_output.stdout}")

    low_bounds, high_bounds = mesh.bounds
    offset = (high_bounds + low_bounds) / 2

    spheres = read_spherization_file(output_file, offset)
    remove_file(output_file)

    return spheres


def check_valid_for_spherization(method, mesh: Trimesh) -> bool:
    MAKE_TREE_PATH = None
    if method == "grid":
        MAKE_TREE_PATH = MAKE_TREE_GRID_PATH
    elif method == "hubbard":
        MAKE_TREE_PATH = MAKE_TREE_HUBBARD_PATH
    elif method == "spawn":
        MAKE_TREE_PATH = MAKE_TREE_SPAWN_PATH
    elif method == "octree":
        MAKE_TREE_PATH = MAKE_TREE_OCTREE_PATH
    else:
        MAKE_TREE_PATH = MAKE_TREE_MEDIAL_PATH

    try:
        command = [str(MAKE_TREE_PATH), '-nopause', '-verify', '-depth', '0']
        compute_spheres_helper(mesh, command, method)
        return True
    except:
        return False


def compute_spheres(
        mesh: Trimesh,
        depth: int = 1,
        branch: int = 8,
        method: str = "medial",  # Can be 'medial', 'grid', 'spawn', 'octree', or 'hubbard'
        testerLevels: int = 2,  # Number of points to represent a sphere when evaluating fit (e.g., -1, 1, 2)
        numCover: int = 5000,  # Number of sample points to cover object with
        minCover: int = 5,  # Minimum number of sample points per triangle
        initSpheres: int = 1000,  # Initial number of spheres in medial axis approximation (for 'medial' method)
        minSpheres: int = 200,  # Minimum number of spheres for each sub-region (for 'medial' method)
        erFact: int = 2,  # Error reduction factor when refining the medial axis (for 'medial' method)
        expand: bool = True,  # Use the EXPAND algorithm (for 'medial' method)
        merge: bool = True,  # Use the MERGE algorithm (for 'medial' method)
        burst: bool = False,  # Use the BURST algorithm (for 'medial' method)
        optimise: bool = True,  # Apply optimization to the sphere-tree
        maxOptLevel: int = 1,  # Maximum level of the sphere-tree to apply optimization (0 = first set only)
        balExcess: float = 0.05,  # Extra error allowed during BALANCE optimization (for 'medial' method)
        verify: bool = False,  # Verify the model is suitable for use

        num_samples: int = 500,  # Number of sample points for Hubbard's method (for 'hubbard' method)
        min_samples: int = 1  # Minimum number of sample points per triangle (for 'hubbard' method)
    ) -> list[Spherization]:

    MAKE_TREE_PATH = None
    if method == "grid":
        MAKE_TREE_PATH = MAKE_TREE_GRID_PATH
    elif method == "hubbard":
        MAKE_TREE_PATH = MAKE_TREE_HUBBARD_PATH
    elif method == "spawn":
        MAKE_TREE_PATH = MAKE_TREE_SPAWN_PATH
    elif method == "octree":
        MAKE_TREE_PATH = MAKE_TREE_OCTREE_PATH
    else:
        MAKE_TREE_PATH = MAKE_TREE_MEDIAL_PATH  # Default to medial if unspecified
    
    # command = [
    #     str(MAKE_TREE_PATH),
    #     '-nopause',
    #     '-verify',
    #     '-branch',
    #     str(branch),
    #     '-depth',
    #     str(depth),
    #     '-testerLevels',
    #     str(tester_level),
    #     '-numCover',
    #     str(num_cover),
    #     '-minCover',
    #     str(min_cover),
    #     '-initSpheres',
    #     str(init_spheres),
    #     '-minSpheres',
    #     str(min_spheres),
    #     '-erFact',
    #     str(er_fact),
    #     '-maxOptLevel',
    #     str(optimization_level),
    #     ]

    # Initial base command for all methods
    command = [
        str(MAKE_TREE_PATH),
        '-nopause',
        '-verify' if verify else '',  # Optional verification flag
        '-branch',
        str(branch),
        '-depth',
        str(depth)
    ]

    # tester_level flag should only be used for 'medial' and 'grid'
    if method in ["medial","grid", "spawn"]:
        command.extend([
            '-testerLevels',
            str(testerLevels)
        ])

    # Method-specific flags
    if method in ["medial", "grid", "spawn"]:
        command.extend([
            '-numCover',
            str(numCover),
            '-minCover',
            str(minCover)
        ])

    if method == "medial":
        command.extend([
            '-initSpheres',
            str(initSpheres),
            '-minSpheres',
            str(minSpheres),
            '-erFact',
            str(erFact),
            '-maxOptLevel',
            str(maxOptLevel)
        ])
    if expand:
        command.append('-expand')
    if merge:
        command.append('-merge')
    if burst:
        command.append('-burst')

    if balExcess > 0:
        command.extend(['-balExcess', str(balExcess)])

    if method == "hubbard":
        command.extend([
            '-numSamples',
            str(num_samples),
            '-minSamples',
            str(min_samples)
        ])

    if optimise and method != "medial":
        command.extend(['-optimise', 'simplex'])  # Simplex optimization applied to non-medial methods


    # Clean up empty flags
    # command = [flag for flag in command if flag]

    # print(command)
    # if expand:
    #     command.append('-expand')
    # if merge:
    #     command.append('-merge')
    # if optimize:
    #     command.extend(['-optimise', 'simplex'])

    return compute_spheres_helper(mesh, command, method)

def simplify(mesh: Trimesh, ratio: float = 0.5, aggressiveness: float = 7.0) -> Trimesh:
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        with tempmesh() as (_, output_path):
            run(
                [
                    str(SIMPLIFY_PATH),
                    str(input_path),
                    str(output_path),
                    str(ratio),
                    str(aggressiveness),
                    ],
                stdout = DEVNULL
                )

            return load_mesh_file(output_path)


def simplify_manifold(mesh: Trimesh, ratio: float = 0.5) -> Trimesh:
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        with tempmesh() as (_, output_path):
            run(
                [
                    str(SIMPLIFY_OLD_PATH),
                    '-i',
                    str(input_path),
                    '-o',
                    str(output_path),
                    '-r',
                    str(ratio),
                    ],
                stdout = DEVNULL
                )

            return load_mesh_file(output_path)


def manifold(mesh: Trimesh, leaves: int = 1000) -> Trimesh:
    _ = mesh.vertex_normals    # Need to compute vertex normals
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        with tempmesh() as (_, output_path):
            run([str(MANIFOLD_OLD_PATH), str(input_path), str(output_path), str(leaves)], stdout = DEVNULL)
            return load_mesh_file(output_path)


def manifold_plus(mesh: Trimesh, depth: int = 8) -> Trimesh:
    _ = mesh.vertex_normals    # Need to compute vertex normals
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        with tempmesh() as (_, output_path):
            run(
                [
                    str(MANIFOLD_OLD_PATH),
                    '--input',
                    str(input_path),
                    '--output',
                    str(output_path),
                    '--depth',
                    str(depth)
                    ],
                stdout = DEVNULL
                )

            return load_mesh_file(output_path)
