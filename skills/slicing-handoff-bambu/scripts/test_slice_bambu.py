"""Smoke tests for the opt-in project export: intent-to-override mapping, profile
selection against a synthetic BBL profile tree, the project_settings.config rewrite
that makes the GUI honour the overrides, and the skip paths (no Bambu binary, no
Bambu printer family). None of these need Bambu Studio installed.
Run: python test_slice_bambu.py"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slice_bambu import (changed_keys, export_project, intent_overrides,  # noqa: E402
                         mark_changed_keys, pick_profiles)

NO_BIN = "/nonexistent/bambu-studio"


def _intent(**kw):
    base = {"printer_family": "bambu_x1c", "nozzle_mm": 0.4, "layer_height_mm": 0.2,
            "bed_type": "textured_pei", "supports": "auto", "brim": "on",
            "filament_slots_logical": [{"role": "primary", "material": "PLA"}]}
    base.update(kw)
    return base


def test_intent_overrides():
    ov, notes = intent_overrides(_intent(), walls=4)
    assert ov == {"enable_support": "1", "support_type": "tree(auto)",
                  "brim_type": "auto_brim", "curr_bed_type": "Textured PEI Plate",
                  "wall_loops": "4"}, ov
    assert notes == [], notes

    ov, notes = intent_overrides(_intent(supports="off", brim="off", bed_type="cool"))
    assert ov == {"enable_support": "0", "brim_type": "no_brim",
                  "curr_bed_type": "Cool Plate"}, ov
    assert "wall_loops" not in ov and "support_type" not in ov

    ov, _ = intent_overrides(_intent(supports="normal", brim="outer"))
    assert ov["support_type"] == "normal(auto)" and ov["brim_type"] == "outer_only", ov

    # Bambu's own bed-type strings pass straight through.
    ov, _ = intent_overrides(_intent(bed_type="High Temp Plate"))
    assert ov["curr_bed_type"] == "High Temp Plate", ov

    # Unknown values are skipped, not guessed, and each one leaves a note.
    ov, notes = intent_overrides(_intent(bed_type="glass", supports="maybe", brim="huge"))
    assert not any(k in ov for k in ("curr_bed_type", "enable_support", "brim_type")), ov
    assert len(notes) == 3 and all("left at profile default" in n for n in notes), notes


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def _fake_bbl(tmp):
    """The slice of Bambu's profile tree the picker relies on, with `inherits`
    chains so the flattening is exercised too."""
    bbl = os.path.join(tmp, "BBL")
    m, p, f = (os.path.join(bbl, d) for d in ("machine", "process", "filament"))
    _write(os.path.join(m, "fdm_x1c_common.json"),
           {"type": "machine", "instantiation": "false",
            "default_print_profile": "0.20mm Standard @BBL X1C",
            "default_filament_profile": ["Bambu PLA Basic @BBL X1C"]})
    _write(os.path.join(m, "Bambu Lab X1 Carbon 0.4 nozzle.json"),
           {"inherits": "fdm_x1c_common", "name": "Bambu Lab X1 Carbon 0.4 nozzle",
            "nozzle_diameter": ["0.4"]})
    _write(os.path.join(m, "Bambu Lab X1 Carbon 0.6 nozzle.json"),
           {"inherits": "fdm_x1c_common", "name": "Bambu Lab X1 Carbon 0.6 nozzle",
            "nozzle_diameter": ["0.6"],
            "default_print_profile": "0.30mm Standard @BBL X1C 0.6 nozzle",
            "default_filament_profile": ["Bambu PLA Basic @BBL X1C 0.6 nozzle"]})
    # P1S is the awkward one: its process presets carry the X1C tag while its
    # filaments carry "P1S 0.4 nozzle", so the picker must follow the machine's
    # defaults rather than a per-family string.
    _write(os.path.join(m, "Bambu Lab P1S 0.4 nozzle.json"),
           {"inherits": "fdm_x1c_common", "name": "Bambu Lab P1S 0.4 nozzle",
            "default_filament_profile": ["Bambu PLA Basic @BBL P1S 0.4 nozzle"]})
    _write(os.path.join(p, "fdm_process_common.json"),
           {"type": "process", "wall_loops": "2", "enable_support": "0",
            "support_type": "tree(auto)"})
    for name, lh in [("0.20mm Standard @BBL X1C", "0.2"),
                     ("0.16mm Optimal @BBL X1C", "0.16"),
                     ("0.16mm High Quality @BBL X1C", "0.16"),
                     ("0.30mm Standard @BBL X1C 0.6 nozzle", "0.3")]:
        _write(os.path.join(p, name + ".json"),
               {"inherits": "fdm_process_common", "name": name, "layer_height": lh})
    # H2D: the default PLA is tagged "H2D", Bambu's PETG Basic "H2D 0.4 nozzle".
    _write(os.path.join(m, "Bambu Lab H2D 0.4 nozzle.json"),
           {"name": "Bambu Lab H2D 0.4 nozzle",
            "default_print_profile": "0.20mm Standard @BBL H2D",
            "default_filament_profile": ["Bambu PLA Basic @BBL H2D"]})
    _write(os.path.join(p, "0.20mm Standard @BBL H2D.json"),
           {"inherits": "fdm_process_common", "layer_height": "0.2"})
    _write(os.path.join(f, "fdm_filament_common.json"), {"type": "filament"})
    for name in ["Bambu PLA Basic @BBL X1C", "Bambu PETG Basic @BBL X1C",
                 "Bambu PETG HF @BBL X1C", "Generic ABS @BBL X1C",
                 "Bambu PLA Basic @BBL X1C 0.6 nozzle", "Bambu PETG Basic @BBL A1",
                 "Bambu PLA Basic @BBL P1S 0.4 nozzle", "Generic PETG HF @BBL P1S 0.4 nozzle",
                 "Bambu PLA Basic @BBL H2D", "Generic PETG @BBL H2D",
                 "Bambu PETG Basic @BBL H2D 0.4 nozzle"]:
        _write(os.path.join(f, name + ".json"),
               {"inherits": "fdm_filament_common", "name": name})
    # Tagged for the machine but declared for another nozzle: must be skipped.
    _write(os.path.join(f, "Bambu ASA @BBL H2D.json"),
           {"name": "Bambu ASA @BBL H2D",
            "compatible_printers": ["Bambu Lab H2D 0.6 nozzle"]})
    _write(os.path.join(f, "Generic ASA @BBL H2D.json"),
           {"name": "Generic ASA @BBL H2D",
            "compatible_printers": ["Bambu Lab H2D 0.4 nozzle", "Bambu Lab H2D 0.6 nozzle"]})
    return bbl


def test_pick_profiles():
    with tempfile.TemporaryDirectory() as tmp:
        bbl = _fake_bbl(tmp)

        names, extra, notes = pick_profiles(bbl, "bambu_x1c", 0.4, 0.2, "PLA")
        assert names == {"machine": "Bambu Lab X1 Carbon 0.4 nozzle",
                         "process": "0.20mm Standard @BBL X1C",
                         "filament": "Bambu PLA Basic @BBL X1C"}, names
        assert extra == {} and notes == [], (extra, notes)

        # Other layer height: the sibling preset with that height, Optimal over
        # High Quality; other material: the Basic preset for the same machine.
        names, extra, _ = pick_profiles(bbl, "bambu_x1c", 0.4, 0.16, "petg")
        assert names["process"] == "0.16mm Optimal @BBL X1C", names
        assert names["filament"] == "Bambu PETG Basic @BBL X1C", names
        assert extra == {}, extra

        # No preset at that height: keep the default and override layer_height.
        names, extra, notes = pick_profiles(bbl, "bambu_x1c", 0.4, 0.28, "PLA")
        assert names["process"] == "0.20mm Standard @BBL X1C", names
        assert extra == {"layer_height": "0.28"}, extra
        assert any("0.28" in n for n in notes), notes

        # No preset for that material: keep the default filament, say so.
        names, _, notes = pick_profiles(bbl, "bambu_x1c", 0.4, 0.2, "TPU")
        assert names["filament"] == "Bambu PLA Basic @BBL X1C", names
        assert any("TPU" in n for n in notes), notes

        # Nozzle changes the machine, and with it the default process and filament.
        names, extra, _ = pick_profiles(bbl, "bambu_x1c", 0.6, 0.3, "PLA")
        assert names == {"machine": "Bambu Lab X1 Carbon 0.6 nozzle",
                         "process": "0.30mm Standard @BBL X1C 0.6 nozzle",
                         "filament": "Bambu PLA Basic @BBL X1C 0.6 nozzle"}, names

        # P1S: X1C-tagged process, P1S-tagged filament, Generic when Bambu has none.
        names, _, _ = pick_profiles(bbl, "bambu_p1s", 0.4, 0.2, "PETG")
        assert names["process"] == "0.20mm Standard @BBL X1C", names
        assert names["filament"] == "Generic PETG HF @BBL P1S 0.4 nozzle", names

        # H2D: the nozzle-suffixed Bambu Basic preset beats the bare-tagged Generic,
        # and a preset declared for another nozzle loses to one declared for this.
        names, _, _ = pick_profiles(bbl, "bambu_h2d", 0.4, 0.2, "PETG")
        assert names["filament"] == "Bambu PETG Basic @BBL H2D 0.4 nozzle", names
        names, _, _ = pick_profiles(bbl, "bambu_h2d", 0.4, 0.2, "ASA")
        assert names["filament"] == "Generic ASA @BBL H2D", names

        # generic maps to the X1C defaults and says so.
        names, _, notes = pick_profiles(bbl, "generic", 0.4, 0.2, "PLA")
        assert names["machine"] == "Bambu Lab X1 Carbon 0.4 nozzle", names
        assert any("generic" in n for n in notes), notes

        for family, nozzle in [("prusa_mk4s", 0.4), ("bambu_x1c", 0.5)]:
            try:
                pick_profiles(bbl, family, nozzle, 0.2, "PLA")
            except ValueError:
                continue
            raise AssertionError(f"{family}/{nozzle} should have been rejected")


def test_changed_keys():
    profile = {"wall_loops": "2", "enable_support": "0", "layer_height": "0.2"}
    overrides = {"wall_loops": "4", "enable_support": "0", "brim_type": "no_brim",
                 "curr_bed_type": "Textured PEI Plate"}
    # Equal to the preset: not a change. Absent from the preset (brim_type): the
    # GUI would fall back to its compiled default, so it counts. curr_bed_type is
    # a project-level setting, not a preset key, so it never enters the diff.
    assert changed_keys(profile, overrides) == ["brim_type", "wall_loops"]


def _fake_project(path, cfg):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("3D/3dmodel.model", "<model/>")
        z.writestr("Metadata/project_settings.config", json.dumps(cfg))
        z.writestr("Metadata/plate_1.png", b"\x89PNG\r\n")


def test_mark_changed_keys():
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = os.path.join(tmp, "raw.3mf"), os.path.join(tmp, "out.3mf")
        cfg = {"wall_loops": "4", "brim_type": "no_brim", "print_settings_id": "x",
               "different_settings_to_system": ["", "", ""]}
        _fake_project(src, cfg)
        mark_changed_keys(src, dst, ["wall_loops", "brim_type"])
        with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst) as zo:
            assert zi.namelist() == zo.namelist()
            for name in zi.namelist():
                if name != "Metadata/project_settings.config":
                    assert zi.read(name) == zo.read(name), name
            out = json.loads(zo.read("Metadata/project_settings.config"))
        # Only the process slot (index 0) is marked; the rest of the config survives.
        assert out["different_settings_to_system"] == ["brim_type;wall_loops", "", ""], out
        assert out["wall_loops"] == "4" and out["print_settings_id"] == "x", out

        # A config without the key gets one shaped [process, filament, printer].
        _fake_project(src, {"wall_loops": "4"})
        mark_changed_keys(src, dst, ["wall_loops"])
        with zipfile.ZipFile(dst) as zo:
            out = json.loads(zo.read("Metadata/project_settings.config"))
        assert out["different_settings_to_system"] == ["wall_loops", "", ""], out


def test_export_project_skips():
    with tempfile.TemporaryDirectory() as tmp:
        model = os.path.join(tmp, "model.3mf")
        _fake_project(model, {})
        # No binary: report it the way --slice does, write nothing.
        r = export_project(model, tmp, _intent(), walls=4, bambu_bin=NO_BIN)
        assert r["exported"] is False and r["project_3mf"] is None, r
        assert "not found" in r["note"] and NO_BIN in r["note"], r
        assert not os.path.exists(os.path.join(tmp, "model.project.3mf"))
        # Non-Bambu printer: refused before the binary is even looked for.
        r = export_project(model, tmp, _intent(printer_family="prusa_mk4s"), bambu_bin=NO_BIN)
        assert r["exported"] is False and "prusa_mk4s" in r["note"], r
        assert "not found" not in r["note"], r


def test_run_handoff_project_flag():
    """The orchestrator wires --project/--walls through: walls lands in print_intent,
    the project block reports the skip, and the bare artifacts are untouched."""
    here = os.path.dirname(os.path.abspath(__file__))
    with tempfile.TemporaryDirectory() as tmp:
        stl = os.path.join(tmp, "box.stl")
        with open(stl, "w") as f:                       # a unit tetrahedron
            f.write("solid t\n")
            for tri in [((0, 0, 0), (1, 0, 0), (0, 1, 0)), ((0, 0, 0), (0, 0, 1), (1, 0, 0)),
                        ((0, 0, 0), (0, 1, 0), (0, 0, 1)), ((1, 0, 0), (0, 0, 1), (0, 1, 0))]:
                f.write("facet normal 0 0 0\nouter loop\n")
                for v in tri:
                    f.write("vertex %g %g %g\n" % v)
                f.write("endloop\nendfacet\n")
            f.write("endsolid t\n")
        out = os.path.join(tmp, "handoff")
        r = subprocess.run([sys.executable, os.path.join(here, "run_handoff.py"), stl,
                            "--out", out, "--printer", "bambu_x1c", "--project",
                            "--walls", "3", "--bambu-bin", NO_BIN],
                           capture_output=True, text=True, timeout=600)
        assert r.returncode == 0, r.stderr[-800:]
        res = json.loads(r.stdout)
        assert res["manifest"]["print_intent"]["walls"] == 3, res["manifest"]["print_intent"]
        assert res["project"]["exported"] is False and "not found" in res["project"]["note"], res
        assert os.path.exists(os.path.join(out, "model.3mf"))
        assert "model.project.3mf" not in res["manifest"]["provenance"]["files"]
        assert not os.path.exists(os.path.join(out, "model.project.3mf"))


if __name__ == "__main__":
    test_intent_overrides()
    test_pick_profiles()
    test_changed_keys()
    test_mark_changed_keys()
    test_export_project_skips()
    test_run_handoff_project_flag()
    print("ok")
