"""One-command setup for Printagent's Python side.

    python3 scripts/bootstrap_env.py --check      what is missing, and whether a
                                                  suitable Python even exists
    python3 scripts/bootstrap_env.py --install    build the environment and install
    python3 scripts/bootstrap_env.py --path       print the recorded interpreter

Nothing here needs the user to activate a virtualenv. The interpreter path is
recorded, and the skills re-execute themselves under it as needed.

Stdlib only, and 3.9-compatible syntax, because the whole point is to run on
whatever Python a newcomer already has.
"""
from __future__ import annotations
import argparse
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from printagent_env import (  # noqa: E402
    CORE_MODULES, DEFAULT_VENV, MIN_PYTHON, RECORD_PATH,
    missing_modules, plugin_root, record_interpreter, recorded_interpreter,
)

VERSION_HELP = {
    "darwin": ("The Python that ships with macOS is 3.9, which is too old for the\n"
               "  geometry kernel. Install a newer one, either from python.org or with\n"
               "  Homebrew:  brew install python@3.12"),
    "linux": ("Install a newer Python from your package manager, for example\n"
              "  sudo apt install python3.12 python3.12-venv"),
    "win32": "Install a newer Python from https://www.python.org/downloads/",
}


def _version_of(python_path):
    try:
        out = subprocess.run(
            [python_path, "-c", "import sys;print('%d.%d' % sys.version_info[:2])"],
            capture_output=True, text=True, timeout=60)
        parts = out.stdout.strip().split(".")
        return (int(parts[0]), int(parts[1])) if len(parts) == 2 else None
    except Exception:
        return None


def find_suitable_python():
    """A Python new enough for build123d. Prefers the one running this script."""
    seen = []
    if sys.version_info[:2] >= MIN_PYTHON:
        return sys.executable, sys.version_info[:2]
    seen.append(sys.executable)

    import shutil
    names = ["python3.14", "python3.13", "python3.12", "python3.11", "python3.10",
             "python3", "python"]
    for name in names:
        path = shutil.which(name)
        if not path or path in seen:
            continue
        seen.append(path)
        ver = _version_of(path)
        if ver and ver >= MIN_PYTHON:
            return path, ver
    for path in ["/opt/homebrew/bin/python3", "/usr/local/bin/python3"]:
        if os.path.exists(path) and path not in seen:
            ver = _version_of(path)
            if ver and ver >= MIN_PYTHON:
                return path, ver
    return None, None


def check():
    root = plugin_root()
    print("Printagent environment check")
    print("  plugin root:  %s" % (root or "NOT FOUND"))

    current = "%d.%d" % sys.version_info[:2]
    ok_now = sys.version_info[:2] >= MIN_PYTHON
    print("  this Python:  %s (%s)" % (current, "new enough" if ok_now else "too old"))

    interp = recorded_interpreter()
    print("  recorded env: %s" % (interp or "none yet"))

    if interp:
        missing = missing_modules(CORE_MODULES, interp)
        if missing is None:
            print("\n  ready: PROBABLY, but the check timed out. The first import "
                  "after\n  an install is slow; rerun --check to confirm.")
            return 0
        if not missing:
            print("\n  ready: YES, the skills will find this automatically")
            return 0
        print("  missing in it: %s" % ", ".join(missing))

    here_missing = missing_modules(CORE_MODULES)
    if not here_missing:
        print("\n  ready: YES, the running interpreter already has everything")
        return 0

    print("  missing here:  %s" % ", ".join(here_missing))
    cand, ver = find_suitable_python()
    if cand:
        print("\n  a suitable Python exists: %s (%d.%d)" % (cand, ver[0], ver[1]))
        print("  next step:  %s %s --install" % (sys.executable, os.path.abspath(__file__)))
    else:
        print("\n  no Python >= %d.%d found." % MIN_PYTHON)
        print("  %s" % VERSION_HELP.get(sys.platform, VERSION_HELP["linux"]))
    print("\n  ready: NO")
    return 1


def install(venv_dir=DEFAULT_VENV):
    root = plugin_root()
    if not root:
        print("Could not locate the plugin root (no requirements.txt above this "
              "script).", file=sys.stderr)
        return 2
    req = os.path.join(root, "requirements.txt")

    python, ver = find_suitable_python()
    if not python:
        print("No Python %d.%d or newer found, and Printagent's geometry kernel "
              "needs one.\n  %s" % (MIN_PYTHON[0], MIN_PYTHON[1],
                                    VERSION_HELP.get(sys.platform, VERSION_HELP["linux"])),
              file=sys.stderr)
        return 2
    print("Using Python %d.%d at %s" % (ver[0], ver[1], python))

    venv_python = os.path.join(venv_dir, "bin", "python")
    if sys.platform == "win32":
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")

    if not os.path.exists(venv_python):
        print("Creating environment at %s ..." % venv_dir)
        r = subprocess.run([python, "-m", "venv", venv_dir])
        if r.returncode != 0:
            print("Could not create the environment. On Debian or Ubuntu this "
                  "usually means the python3-venv package is missing.", file=sys.stderr)
            return r.returncode
    else:
        print("Reusing the environment at %s" % venv_dir)

    print("Installing packages (about 700 MB, this takes a few minutes) ...")
    subprocess.run([venv_python, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    r = subprocess.run([venv_python, "-m", "pip", "install", "-r", req])
    if r.returncode != 0:
        print("\nThe install failed. The output above says why; a network drop is "
              "the usual cause, and rerunning is safe.", file=sys.stderr)
        return r.returncode

    # pip succeeding is the strong signal. The import probe is a confirmation, and
    # a cold OCCT import can outrun any sensible timeout, so an unfinished probe
    # must not turn a good install into a reported failure.
    missing = missing_modules(CORE_MODULES, venv_python)
    if missing:
        print("\nInstalled, but these still will not import: %s" % ", ".join(missing),
              file=sys.stderr)
        return 1
    if missing is None:
        print("\nInstalled. The import check did not finish in time, which is normal "
              "the\nfirst time, so verify with --check when convenient.")

    record_interpreter(venv_python, venv_dir)
    print("\nDone. Recorded %s" % RECORD_PATH)
    print("The skills use this automatically. There is nothing to activate.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Set up Printagent's Python packages.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--install", action="store_true")
    g.add_argument("--path", action="store_true")
    ap.add_argument("--venv", default=DEFAULT_VENV, help="where to build the environment")
    a = ap.parse_args()

    if a.check:
        return check()
    if a.path:
        interp = recorded_interpreter()
        print(interp or "")
        return 0 if interp else 1
    return install(a.venv)


if __name__ == "__main__":
    sys.exit(main())
