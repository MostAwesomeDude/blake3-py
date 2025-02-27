#! /usr/bin/env python3

import os
import platform
import sys
from pathlib import Path
import subprocess

ROOT = Path(__file__).parent.parent.parent

# For macOS and Windows, we run Maturin against the Python interpreter that's
# been installed and configured for this CI run, i.e. the one that's running
# this script. (There are generally several versions installed by default, but
# that's not guaranteed.) For Linux, in order to get "manylinux" compatibility
# right, we need to run Maturin in a special Docker container. We hardcode
# paths to specific interpreter versions, based on where things are installed
# in this container. Our GitHub config has no effect on the the container, so
# we could build all the wheels in one job, but we stick to one-wheel-per-job
# for consistency.
if platform.system() == "Linux":
    version_path_components = {
        (3, 7): "cp37-cp37m",
        (3, 8): "cp38-cp38",
        (3, 9): "cp39-cp39",
        (3, 10): "cp310-cp310",
        (3, 11): "cp311-cp311",
        # This list needs to be kept in sync with:
        #   - push.yml (rust_impl and c_impl)
        #   - tag.yml
    }
    version_component = version_path_components[sys.version_info[:2]]
    interpreter_path = "/opt/python/" + version_component + "/bin/python"
    # See https://github.com/PyO3/maturin#manylinux-and-auditwheel
    command = [
        "docker",
        "run",
        "--rm",
        "--volume=" + os.getcwd() + ":/io",
        "--env=BLAKE3_CI=1",  # don't allow fallbacks for missing AVX-512 support
        "ghcr.io/pyo3/maturin",
        "build",
        "--release",
        "--interpreter",
        interpreter_path,
    ]
    subprocess.run(command, check=True)
else:
    command = [
        "maturin",
        "build",
        "--release",
        "--interpreter",
        sys.executable,
    ]
    subprocess.run(command, check=True)

wheels = [x for x in (ROOT / "target" / "wheels").iterdir()]
if len(wheels) != 1:
    raise RuntimeError("expected one wheel, found " + repr(wheels))

with open(os.environ["GITHUB_OUTPUT"], "a") as output:
    output.write(f"wheel_path={str(wheels[0])}\n")
