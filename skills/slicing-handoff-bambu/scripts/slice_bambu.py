"""Optional: slice model.3mf with the Bambu Studio CLI, or export it as a Bambu Studio
project that opens print-ready. Slicing only; printing is downstream.
Always uses a per-plate timeout and a sandboxed temp dir."""
from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

# Used when the caller passes no profiles; the CLI segfaults with none loaded.
DEFAULT_PROFILES = {"machine": "Bambu Lab X1 Carbon 0.4 nozzle",
                    "process": "0.20mm Standard @BBL X1C",
                    "filament": "Bambu PLA Basic @BBL X1C"}

# Standard install locations, tried in order when the caller passes no explicit
# path. Most users never have to name the binary; --bambu-bin stays the override
# for a non-standard install.
STANDARD_BINS = [
    "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
    "~/Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
    "/usr/bin/bambu-studio",
    "/usr/local/bin/bambu-studio",
    "/opt/bambu-studio/bambu-studio",
    "~/.local/bin/bambu-studio",
]

# print_intent.printer_family -> machine preset prefix; the nozzle completes the name.
BAMBU_MACHINES = {"bambu_x1c": "Bambu Lab X1 Carbon", "bambu_p1s": "Bambu Lab P1S",
                  "bambu_a1": "Bambu Lab A1", "bambu_h2d": "Bambu Lab H2D"}

# print_intent vocabulary -> Bambu Studio config values. Bambu's own bed-type
# strings pass through untouched. Anything not listed is left at the preset's
# default and reported, never guessed.
BED_TYPES = {"textured_pei": "Textured PEI Plate", "cool": "Cool Plate",
             "cool_plate": "Cool Plate", "engineering": "Engineering Plate",
             "high_temp": "High Temp Plate", "smooth_pei": "High Temp Plate",
             "supertack": "Supertack Plate"}
SUPPORTS = {"off": ("0", None), "none": ("0", None), "no": ("0", None),
            "auto": ("1", "tree(auto)"), "on": ("1", "tree(auto)"),
            "yes": ("1", "tree(auto)"), "tree": ("1", "tree(auto)"),
            "normal": ("1", "normal(auto)")}
BRIMS = {"on": "auto_brim", "auto": "auto_brim", "yes": "auto_brim",
         "off": "no_brim", "none": "no_brim", "no": "no_brim",
         "outer": "outer_only", "inner": "inner_only", "both": "outer_and_inner"}

# Written into the project config but owned by the project, not by any preset:
# the GUI reads these from the file directly, so they never belong in a preset diff.
PROJECT_KEYS = {"curr_bed_type"}

_PROCESS_NAME = re.compile(r"^(\d+\.\d+)mm (.+?) @BBL (.+)$")
_FILAMENT_NAME = re.compile(r"^(Bambu|Generic) (.+?) @BBL (.+)$")


def find_bambu_bin(bambu_bin=None):
    """Resolve the Bambu Studio CLI. An explicit path or command name wins; then
    PATH; then the standard install locations. Returns None when nothing exists."""
    if bambu_bin:
        found = shutil.which(bambu_bin)
        if found:
            return found
        expanded = os.path.expanduser(bambu_bin)
        return expanded if os.path.exists(expanded) else None
    found = shutil.which("bambu-studio")
    if found:
        return found
    for cand in STANDARD_BINS:
        expanded = os.path.expanduser(cand)
        if os.path.exists(expanded):
            return expanded
    return None


def _bbl_dir(binp):
    """Bambu's bundled vendor presets live beside the binary."""
    return os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(binp)),
                                         "..", "Resources", "profiles", "BBL"))


def load_profile(bbl_dir, folder, name):
    """A bundled preset with its `inherits` chain merged in. The CLI does not
    resolve the chain itself, so every preset handed to it goes through here."""
    with open(os.path.join(bbl_dir, folder, name + ".json")) as f:
        data = json.load(f)
    parent = data.pop("inherits", None)
    if parent:
        base = load_profile(bbl_dir, folder, parent)
        base.update(data)
        return base
    return data


def _flatten_profile(bbl_dir, folder, name, out_dir, overrides=None):
    """Write the merged preset as one JSON the CLI can load. `overrides` are
    written into it; that is how print_intent reaches a process preset."""
    data = load_profile(bbl_dir, folder, name)
    if overrides:
        data.update(overrides)
    out = os.path.join(out_dir, f"{folder}_{name}.json".replace(" ", "_"))
    with open(out, "w") as f:
        json.dump(data, f)
    return out


def _cli_failure(r):
    """The CLI's error lines, or its last words, for a note."""
    text = (r.stderr or "") + (r.stdout or "")
    errs = [ln for ln in text.splitlines() if "error" in ln.lower()]
    return ("\n".join(errs) or text.strip())[-400:] or f"exit code {r.returncode}"


def slice_bambu(model_3mf, out_dir, bambu_bin=None,
                settings=None, filaments=None, mstpp=300, timeout=900):
    binp = find_bambu_bin(bambu_bin)
    if binp is None:
        where = bambu_bin if bambu_bin else "PATH or a standard install location"
        return {"sliced": False, "note": f"Bambu Studio CLI not found ({where}); "
                                         f"install it, pass --bambu-bin, or skip --slice"}
    # The CLI chdirs mid-run, so relative paths break; --export-3mf must be absolute.
    out_gcode = os.path.abspath(os.path.join(out_dir, "model.gcode.3mf"))

    with tempfile.TemporaryDirectory() as tmp:
        if not settings or not filaments:
            bbl = _bbl_dir(binp)
            if not os.path.isdir(bbl):
                return {"sliced": False,
                        "note": f"no profiles passed and none found at {bbl}; slicing "
                                f"without machine/process/filament settings crashes the CLI"}
            if not settings:
                settings = [_flatten_profile(bbl, "machine", DEFAULT_PROFILES["machine"], tmp),
                            _flatten_profile(bbl, "process", DEFAULT_PROFILES["process"], tmp)]
            if not filaments:
                filaments = [_flatten_profile(bbl, "filament", DEFAULT_PROFILES["filament"], tmp)]

        # --orient/--arrange take explicit values in Studio >= 02.07 (0-disable, 1-enable)
        cmd = [binp, "--slice", "0", "--orient", "1", "--arrange", "1",
               "--mstpp", str(mstpp),
               "--load-settings", ";".join(settings),
               "--load-filaments", ";".join(filaments),
               "--export-3mf", out_gcode, os.path.abspath(model_3mf)]
        env = {**os.environ, "TMPDIR": tmp}
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return {"sliced": False, "note": "slice timed out (pathological mesh?)"}

    ok = r.returncode == 0 and os.path.exists(out_gcode)
    return {"sliced": ok, "gcode_3mf": out_gcode if ok else None,
            "note": "ok" if ok else _cli_failure(r)}


# --- project export -------------------------------------------------------------
# Bambu Studio opens a bare 3MF with "The 3mf file has invalid config, load geometry
# data only" and drops every setting it carried, so print_intent never reaches the
# slicer. A project 3MF is one the GUI wrote itself, and it opens as-is. The CLI
# can write one (--export-3mf without --slice), with two catches handled below:
# the bundled presets must be flattened first, and different_settings_to_system
# must name the overridden keys, or the GUI trusts its stock preset over the file.

def intent_overrides(intent, walls=None):
    """Process-preset overrides that express the print_intent hints, plus a note
    for every hint with no Bambu equivalent (those stay at the preset's default)."""
    overrides, notes = {}, []

    def unknown(field, value):
        notes.append(f"{field} {value!r} has no Bambu mapping; left at profile default")

    supports = intent.get("supports")
    if supports is not None:
        found = SUPPORTS.get(str(supports).lower())
        if found is None:
            unknown("supports", supports)
        else:
            overrides["enable_support"] = found[0]
            if found[1]:
                overrides["support_type"] = found[1]
    brim = intent.get("brim")
    if brim is not None:
        found = BRIMS.get(str(brim).lower())
        if found is None:
            unknown("brim", brim)
        else:
            overrides["brim_type"] = found
    bed = intent.get("bed_type")
    if bed is not None:
        found = bed if bed in BED_TYPES.values() else BED_TYPES.get(str(bed).lower())
        if found is None:
            unknown("bed_type", bed)
        else:
            overrides["curr_bed_type"] = found
    if walls is not None:
        overrides["wall_loops"] = str(int(walls))
    return overrides, notes


def _preset_names(bbl_dir, folder):
    d = os.path.join(bbl_dir, folder)
    return sorted(n[:-5] for n in os.listdir(d) if n.endswith(".json"))


def _sibling_tags(tag, nozzle_mm):
    """The tags a sibling preset may carry. Bambu is not consistent: for the H2D
    0.4 the default PLA preset is tagged "H2D" while PETG Basic is tagged
    "H2D 0.4 nozzle", so both the bare tag and the nozzle-suffixed one count."""
    base = re.sub(r" \d+(\.\d+)? nozzle$", "", tag)
    return {base, f"{base} {nozzle_mm:g} nozzle"}


def _fits_machine(bbl_dir, folder, name, machine):
    """A preset that declares compatible printers must list this machine; one
    that declares none is taken at its tag's word."""
    compat = load_profile(bbl_dir, folder, name).get("compatible_printers") or []
    return not compat or machine in compat


def pick_profiles(bbl_dir, printer_family, nozzle_mm, layer_height_mm, material):
    """Choose the machine, process, and filament presets for a print_intent.

    Starts from the machine preset's own defaults, then swaps in the sibling
    process preset at the requested layer height and the sibling filament for the
    requested material. Siblings are matched on the tag in the default preset's
    name, because the tag is not derivable from the family: the P1S uses
    X1C-tagged process presets but P1S-tagged filaments.

    Returns (names, extra_overrides, notes). Raises ValueError when the family is
    not a Bambu printer or the nozzle has no machine preset."""
    notes = []
    family = printer_family
    if family == "generic":
        family = "bambu_x1c"
        notes.append("printer_family generic: using Bambu Lab X1 Carbon presets")
    prefix = BAMBU_MACHINES.get(family)
    if prefix is None:
        raise ValueError(f"printer_family {printer_family!r} is not a Bambu printer; "
                         f"project export supports {', '.join(sorted(BAMBU_MACHINES))}")
    machine = f"{prefix} {nozzle_mm:g} nozzle"
    if not os.path.exists(os.path.join(bbl_dir, "machine", machine + ".json")):
        raise ValueError(f"no machine preset {machine!r} under {bbl_dir}")
    mdata = load_profile(bbl_dir, "machine", machine)
    process = mdata["default_print_profile"]
    filament = mdata["default_filament_profile"]
    if isinstance(filament, list):
        filament = filament[0]
    extra = {}

    # Process: the sibling at the requested layer height (Standard first, then
    # Optimal, then whatever sorts first), else the default with the height overridden.
    m = _PROCESS_NAME.match(process)
    if m and abs(float(m.group(1)) - layer_height_mm) > 1e-6:
        tags, cands = _sibling_tags(m.group(3), nozzle_mm), []
        for n in _preset_names(bbl_dir, "process"):
            pm = _PROCESS_NAME.match(n)
            if (pm and pm.group(3) in tags and abs(float(pm.group(1)) - layer_height_mm) <= 1e-6
                    and _fits_machine(bbl_dir, "process", n, machine)):
                quality = pm.group(2)
                cands.append(((quality != "Standard", "Optimal" not in quality, n), n))
        if cands:
            process = min(cands)[1]
    pdata = load_profile(bbl_dir, "process", process)
    if abs(float(pdata.get("layer_height", layer_height_mm)) - layer_height_mm) > 1e-6:
        extra["layer_height"] = f"{layer_height_mm:g}"
        notes.append(f"no process preset at {layer_height_mm:g} mm for {machine}; "
                     f"using {process!r} with layer_height overridden")

    # Filament: the same machine tag, the requested material as the product's first
    # word (so PLA never matches PLA-CF), Bambu Basic before Bambu before Generic.
    fm = _FILAMENT_NAME.match(filament)
    mat = str(material).upper()
    if fm and fm.group(2).split()[0].upper() != mat:
        tags, cands = _sibling_tags(fm.group(3), nozzle_mm), []
        for n in _preset_names(bbl_dir, "filament"):
            nm = _FILAMENT_NAME.match(n)
            if (nm and nm.group(3) in tags and nm.group(2).split()[0].upper() == mat
                    and _fits_machine(bbl_dir, "filament", n, machine)):
                vendor, product = nm.group(1), nm.group(2)
                cands.append(((vendor != "Bambu", "Basic" not in product,
                               product.upper() != mat, n), n))
        if cands:
            filament = min(cands)[1]
        else:
            notes.append(f"no {mat} filament preset for {machine}; left at {filament!r}")
    return {"machine": machine, "process": process, "filament": filament}, extra, notes


def changed_keys(profile, overrides):
    """The process-preset keys an override actually changes. Equal to the preset:
    not a change. Absent from the preset: the GUI would use its compiled default,
    so it counts. Project-level keys are never part of a preset diff."""
    return sorted(k for k, v in overrides.items()
                  if k not in PROJECT_KEYS and profile.get(k) != v)


def mark_changed_keys(src_3mf, dst_3mf, keys):
    """Copy a CLI-exported project, naming `keys` in different_settings_to_system[0]
    (the process slot; filaments and the printer follow). The CLI leaves the list
    empty, and the GUI then trusts the stock preset over the values in the file."""
    with zipfile.ZipFile(src_3mf) as zi, \
            zipfile.ZipFile(dst_3mf, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            data = zi.read(it.filename)
            if it.filename == "Metadata/project_settings.config":
                cfg = json.loads(data)
                diff = list(cfg.get("different_settings_to_system") or [])
                diff += [""] * (3 - len(diff))
                diff[0] = ";".join(sorted(keys))
                cfg["different_settings_to_system"] = diff
                data = json.dumps(cfg, indent=4).encode()
            zo.writestr(it, data)


def export_project(model_3mf, out_dir, intent, walls=None, bambu_bin=None,
                   keep_layout=False, timeout=900):
    """Write model.project.3mf beside model.3mf: the same geometry as a Bambu Studio
    project carrying the print_intent hints as real preset overrides, so the GUI
    opens it print-ready instead of as bare geometry. Returns a dict shaped like
    slice_bambu's: exported, project_3mf, note, plus the presets and overrides used."""
    skipped = {"exported": False, "project_3mf": None}
    family = intent.get("printer_family", "generic")
    if family != "generic" and family not in BAMBU_MACHINES:
        return {**skipped, "note": f"printer_family {family!r} is not a Bambu printer; "
                                   f"project export supports "
                                   f"{', '.join(sorted(BAMBU_MACHINES))} and generic (as X1C)"}
    binp = find_bambu_bin(bambu_bin)
    if binp is None:
        where = bambu_bin if bambu_bin else "PATH or a standard install location"
        return {**skipped, "note": f"Bambu Studio CLI not found ({where}); install it, "
                                   f"pass --bambu-bin, or skip --project"}
    bbl = _bbl_dir(binp)
    if not os.path.isdir(bbl):
        return {**skipped, "note": f"no bundled presets found at {bbl}; a project needs "
                                   f"Bambu's machine/process/filament presets"}

    slots = intent.get("filament_slots_logical") or []
    material = (slots[0].get("material") if slots else None) or "PLA"
    try:
        names, extra, notes = pick_profiles(bbl, family, float(intent.get("nozzle_mm") or 0.4),
                                            float(intent.get("layer_height_mm") or 0.2), material)
    except ValueError as e:
        return {**skipped, "note": str(e)}
    overrides, more = intent_overrides(intent, walls)
    overrides.update(extra)
    notes += more
    changed = changed_keys(load_profile(bbl, "process", names["process"]), overrides)

    out = os.path.abspath(os.path.join(out_dir, "model.project.3mf"))
    with tempfile.TemporaryDirectory() as tmp:
        settings = [_flatten_profile(bbl, "machine", names["machine"], tmp),
                    _flatten_profile(bbl, "process", names["process"], tmp, overrides)]
        filaments = [_flatten_profile(bbl, "filament", names["filament"], tmp)]
        raw = os.path.join(tmp, "raw.3mf")
        # --orient 0: the print pose was chosen upstream and must survive. Arranging
        # centres a lone part on the plate (unarranged, it sits at the bed corner);
        # a hand-laid multi-object plate keeps its layout with keep_layout.
        cmd = [binp, "--orient", "0", "--arrange", "0" if keep_layout else "1",
               "--load-settings", ";".join(settings),
               "--load-filaments", ";".join(filaments),
               "--export-3mf", raw, os.path.abspath(model_3mf)]
        env = {**os.environ, "TMPDIR": tmp}
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return {**skipped, "note": "project export timed out (pathological mesh?)"}
        if r.returncode != 0 or not os.path.exists(raw):
            return {**skipped, "note": _cli_failure(r)}
        mark_changed_keys(raw, out, changed)
    return {"exported": True, "project_3mf": out, "profiles": names,
            "overrides": overrides, "marked_changed": changed,
            "note": "; ".join(notes) or "ok"}
