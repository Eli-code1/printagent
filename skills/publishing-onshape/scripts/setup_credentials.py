"""Guided first-run setup for Onshape API keys. Stdlib only.

Three modes, split so an agent can drive setup without ever seeing a secret:

    --check    report whether usable keys exist. Prints status only, never values.
    --instructions  print the exact steps and the command the USER runs themselves.
    --write    interactive prompt (getpass); writes ~/.config/onshape/credentials 0600.
    --verify   live API call proving the keys work. Prints the account name only.

The agent runs --check, --instructions, and --verify. It must NOT run --write and
must never ask the user to paste keys into the chat: a secret in the transcript is
a secret in the model's context and in the session log. --write exists so the user
can run it in their own terminal, where the secret goes straight to disk.
"""
from __future__ import annotations
import argparse
import os
import stat
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from onshape_client import CRED_PATHS, request  # noqa: E402

PORTAL = "https://cad.onshape.com/user/developer"
PRIMARY = CRED_PATHS[0]


def _read_file_keys(path):
    kv = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    kv[k.strip()] = v.strip().strip('"')
    except OSError:
        return {}
    return kv


def check():
    """Report credential status without revealing any value."""
    env_ok = bool(os.environ.get("ONSHAPE_ACCESS_KEY")) and \
        bool(os.environ.get("ONSHAPE_SECRET_KEY"))
    found = []
    for path in CRED_PATHS:
        if not os.path.exists(path):
            continue
        kv = _read_file_keys(path)
        complete = bool(kv.get("ONSHAPE_ACCESS_KEY")) and bool(kv.get("ONSHAPE_SECRET_KEY"))
        mode = stat.S_IMODE(os.stat(path).st_mode)
        found.append((path, complete, mode))

    print("Onshape credential check")
    print(f"  environment variables: {'set' if env_ok else 'not set'}")
    if not found:
        print("  credentials file:      none found")
    for path, complete, mode in found:
        state = "complete" if complete else "present but missing a key"
        warn = "" if mode == 0o600 else f"  <- permissions are {mode:o}, should be 600"
        print(f"  credentials file:      {path} ({state}){warn}")

    usable = env_ok or any(c for _, c, _ in found)
    print(f"\n  usable keys: {'YES' if usable else 'NO'}")
    if not usable:
        print("  next step: run this script with --instructions")
    return 0 if usable else 1


def instructions():
    """Print steps plus the command the user runs themselves."""
    print(f"""Set up Onshape API keys (one time, about two minutes)

1. Open the Onshape developer portal and sign in:
     {PORTAL}

2. Open the "API keys" tab (the page starts on "Overview"), then click the
   blue "Create new API key" button. Tick at least read and write scopes.
   Delete scope is optional; without it, reuse documents with --url instead
   of recreating them.

3. Onshape shows the secret key EXACTLY ONCE. Keep the tab open.

4. In your own terminal (not through the chat), run:

     python3 {os.path.abspath(__file__)} --write

   It prompts for both keys, hides the secret as you type, and writes
     {PRIMARY}
   with 0600 permissions.

5. Back here, confirm it worked:

     python3 {os.path.abspath(__file__)} --verify

Do not paste the keys into the chat. Anything in the transcript is in the
model's context and in the session log; step 4 keeps the secret off both.""")
    return 0


def write():
    """Interactive write. Meant for the user's own terminal."""
    import getpass
    if not sys.stdin.isatty():
        print("--write needs an interactive terminal, so the secret is never echoed\n"
              "or captured. Run it yourself in a terminal, or see --instructions.",
              file=sys.stderr)
        return 2

    print(f"Keys come from {PORTAL}\n")
    access = input("Access key: ").strip()
    secret = getpass.getpass("Secret key (hidden): ").strip()
    if not access or not secret:
        print("Both keys are required; nothing written.", file=sys.stderr)
        return 2

    target = PRIMARY
    os.makedirs(os.path.dirname(target), exist_ok=True)
    existing = _read_file_keys(target)
    if existing.get("ONSHAPE_ACCESS_KEY") or existing.get("ONSHAPE_SECRET_KEY"):
        reply = input(f"\n{target} already has keys. Overwrite? [y/N] ").strip().lower()
        if reply != "y":
            print("Left unchanged.")
            return 0

    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("# Onshape API keys. Never commit this file.\n")
        f.write(f"ONSHAPE_ACCESS_KEY={access}\n")
        f.write(f"ONSHAPE_SECRET_KEY={secret}\n")
    os.chmod(target, 0o600)
    print(f"\nWrote {target} (permissions 600).")
    print("Now confirm with: python3 " + os.path.abspath(__file__) + " --verify")
    return 0


def verify():
    """One live API call. Prints the account name, never a key."""
    try:
        info = request("GET", "/api/v6/users/sessioninfo")
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        name = type(e).__name__
        status = getattr(e, "status", None)
        if status == 401:
            print("Keys rejected (HTTP 401). The access or secret key is wrong, or the\n"
                  "key was revoked. Create a new pair and rerun --write.", file=sys.stderr)
        else:
            print(f"Could not reach Onshape ({name}). Check the network and retry.",
                  file=sys.stderr)
        return 1

    # The 200 itself is the proof the keys authenticate. Profile fields come back
    # empty for API-key sessions on some accounts, so treat them as a bonus.
    who = (info.get("name") or info.get("email") or "").strip()
    if who:
        print(f"Onshape credentials work. Signed in as: {who}")
    else:
        print("Onshape credentials work. The account profile fields come back empty "
              "for API-key sessions, which is normal.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Guided Onshape API key setup.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="report status, no values")
    g.add_argument("--instructions", action="store_true", help="print the setup steps")
    g.add_argument("--write", action="store_true", help="interactive write (user's terminal)")
    g.add_argument("--verify", action="store_true", help="one live API call")
    a = ap.parse_args()

    if a.check:
        return check()
    if a.instructions:
        return instructions()
    if a.write:
        return write()
    return verify()


if __name__ == "__main__":
    sys.exit(main())
