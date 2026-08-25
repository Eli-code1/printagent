"""Make the geometry skills run under an interpreter that actually has their
dependencies, so nobody has to understand virtualenv activation.

Entry-point scripts call `ensure()` before importing trimesh or build123d. If the
running interpreter already has the packages, it returns immediately and nothing
changes. If it does not, it re-executes the same script under the interpreter
recorded by `bootstrap_env.py`. If no such interpreter exists, it exits with a
plain-language message naming the one command that fixes it, instead of letting
a ModuleNotFoundError traceback reach the user.

Stdlib only. This module must import cleanly on the oldest Python a user might
have, which on a stock Mac is 3.9, so no 3.10+ syntax here.
"""
from __future__ import annotations
import json
import os
import sys

MIN_PYTHON = (3, 10)
DEFAULT_VENV = os.path.expanduser("~/printagent-env")
RECORD_PATH = os.path.expanduser("~/.config/printagent/interpreter.json")
# Import names, not distribution names: rtree imports as `rtree`, lxml as `lxml`.
CORE_MODULES = ["build123d", "trimesh", "numpy", "scipy", "rtree",
                "networkx", "lxml", "shapely"]
_REENTRY_FLAG = "PRINTAGENT_ENV_REEXEC"


def plugin_root(start=None):
    """Walk up from `start` to the directory holding requirements.txt."""
    d = os.path.dirname(os.path.abspath(start or __file__))
    while True:
        if os.path.exists(os.path.join(d, "requirements.txt")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def record_interpreter(python_path, venv_dir=None):
    os.makedirs(os.path.dirname(RECORD_PATH), exist_ok=True)
    payload = {"python": python_path, "venv": venv_dir or ""}
    with open(RECORD_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    return RECORD_PATH


def recorded_interpreter():
    """The interpreter bootstrap_env.py last set up, if it still exists."""
    try:
        with open(RECORD_PATH) as f:
            path = json.load(f).get("python", "")
    except (OSError, ValueError):
        path = ""
    if path and os.path.exists(path):
        return path
    # Fall back to the conventional venv location even with no record, so a user
    # who followed the README by hand is still picked up.
    for candidate in (os.path.join(DEFAULT_VENV, "bin", "python"),
                      os.path.join(DEFAULT_VENV, "Scripts", "python.exe")):
        if os.path.exists(candidate):
            return candidate
    return None


def missing_modules(modules=None, python_path=None, timeout=600):
    """Which of `modules` the interpreter cannot import.

    Returns a list; empty means ready. Returns None when the probe itself could
    not be completed, which is NOT the same as the modules being absent. The
    first import of the OCCT kernel after a fresh install is slow enough to hit
    a short timeout, and reporting that as "nothing is installed" would tell a
    user their successful install had failed.
    """
    mods = list(modules or CORE_MODULES)
    if python_path is None or os.path.abspath(python_path) == os.path.abspath(sys.executable):
        missing = []
        for m in mods:
            try:
                __import__(m)
            except ImportError:
                missing.append(m)
        return missing
    import subprocess
    code = ("import json,sys\nmissing=[]\n"
            "for m in %r:\n"
            "    try: __import__(m)\n"
            "    except ImportError: missing.append(m)\n"
            "print(json.dumps(missing))" % (mods,))
    try:
        out = subprocess.run([python_path, "-c", code], capture_output=True,
                             text=True, timeout=timeout)
    except Exception:
        return None
    text = (out.stdout or "").strip()
    if out.returncode != 0 or not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def _setup_message(missing):
    root = plugin_root() or "the printagent plugin directory"
    boot = os.path.join(root, "scripts", "bootstrap_env.py")
    return (
        "Printagent needs its Python packages before this step can run.\n"
        "  missing: %s\n\n"
        "Set them up once with:\n\n"
        "    %s %s --install\n\n"
        "That builds a private environment at %s and installs everything.\n"
        "It downloads roughly 700 MB, so give it a few minutes. You do not need\n"
        "to activate anything afterwards; the skills find it on their own."
        % (", ".join(missing), sys.executable, boot, DEFAULT_VENV)
    )


def ensure(modules=None, quiet=True):
    """Guarantee the current process can import `modules`, or exit cleanly.

    Returns None when the running interpreter is already usable. Otherwise
    re-executes this script under the recorded interpreter and does not return.
    """
    missing = missing_modules(modules)
    if not missing:
        return

    if os.environ.get(_REENTRY_FLAG):
        # Already re-executed once and still short. Do not loop.
        sys.exit(_setup_message(missing))

    target = recorded_interpreter()
    if target and os.path.abspath(target) != os.path.abspath(sys.executable):
        probe = missing_modules(modules, target)
        # probe is None when it could not be determined. The recorded interpreter
        # is still the best candidate, so hand over anyway; the reentry flag stops
        # this from looping if it turns out to be short too.
        if probe is None or not probe:
            env = dict(os.environ)
            env[_REENTRY_FLAG] = "1"
            if not quiet:
                sys.stderr.write("printagent: switching to %s\n" % target)
            script = os.path.abspath(sys.argv[0])
            os.execve(target, [target, script] + sys.argv[1:], env)

    sys.exit(_setup_message(missing))
