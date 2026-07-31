#!/usr/bin/env python3

from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


field_test = load_script("field_test")
verify_workflow = load_script("verify_workflow")
adv360_action = load_script("adv360_action")
manage_host = load_script("manage_host")


class FieldTestTests(unittest.TestCase):
    def row(self, day: int, *, os_name: str = "macos", minutes: int = 60, awkward: str = "", planned: str = "") -> dict[str, str]:
        return {
            "timestamp": f"2026-07-{day:02d}T12:00:00+02:00", "os": os_name, "minutes": str(minutes),
            "thumb_misfires": "0", "layer_errors": "0", "shortcut_mismatches": "0", "macro_output_errors": "0", "macro_output_measured": "yes",
            "awkward_symbols": awkward, "planned_corrections": planned, "notes": "test",
        }

    def run_report(self, path: Path) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(ROOT / "scripts/field_test.py"), "report", "--log", str(path), "--strict"], text=True, capture_output=True)

    def test_seven_one_minute_days_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            field_test.write_rows(path, [self.row(day, os_name="linux" if day % 2 == 0 else "macos", minutes=1) for day in range(1, 8)])
            result = self.run_report(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PENDING: total time >= 420 minutes", result.stdout)

    def test_zero_minutes_reports_clean_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            rows = [self.row(day) for day in range(1, 8)] + [self.row(8, os_name="linux", minutes=0)]
            field_test.write_rows(path, rows)
            result = self.run_report(path)
            self.assertEqual(result.returncode, 2)
            self.assertIn("minutes must be greater than zero", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_planned_recurring_symbol_can_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            rows = [self.row(day, os_name="linux" if day % 2 == 0 else "macos", awkward="_", planned="_" if day == 1 else "") for day in range(1, 8)]
            field_test.write_rows(path, rows)
            result = self.run_report(path)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("FIELD TEST PASS", result.stdout)

    def test_macro_output_error_blocks_strict_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            rows = [self.row(day, os_name="linux" if day % 2 == 0 else "macos") for day in range(1, 8)]
            rows[3]["macro_output_errors"] = "1"
            field_test.write_rows(path, rows)
            result = self.run_report(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PENDING: zero macro output errors", result.stdout)

    def test_previous_field_log_migrates_macro_errors_to_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            row = self.row(1)
            row.pop("macro_output_errors")
            row.pop("macro_output_measured")
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=field_test.PRE_MACRO_FIELDS)
                writer.writeheader()
                writer.writerow(row)
            field_test.ensure_log(path)
            migrated = field_test.read_rows(path)
            self.assertEqual(migrated[0]["macro_output_errors"], "0")
            self.assertEqual(migrated[0]["macro_output_measured"], "no")
            self.assertEqual(path.read_text().splitlines()[0].split(","), field_test.FIELDS)

    def test_pre_macro_field_sessions_cannot_pass_strict_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            rows = []
            for day in range(1, 8):
                row = self.row(day, os_name="linux" if day % 2 == 0 else "macos")
                row.pop("macro_output_errors")
                row.pop("macro_output_measured")
                rows.append(row)
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=field_test.PRE_MACRO_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            result = self.run_report(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PENDING: macro output measured in every session", result.stdout)

    def test_log_option_works_after_subcommand(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            result = subprocess.run([sys.executable, str(ROOT / "scripts/field_test.py"), "init", "--log", str(path)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(path.exists())


class WorkflowVerifierTests(unittest.TestCase):
    def test_protocol_has_eight_modified_f13_f20_actions(self) -> None:
        protocol = verify_workflow.check_protocol()
        self.assertEqual([action["name"] for action in protocol["actions"]], verify_workflow.ACTIONS)
        self.assertEqual(protocol["actions"][-1]["signal"], "Alt+F20")

    def test_keymap_semantics(self) -> None:
        verify_workflow.check_keymap()

    def test_speed_profile_contract(self) -> None:
        text = (ROOT / "config/adv360.keymap").read_text()
        sym = verify_workflow.layer_rows(text, "layer_sym")

        expected_macros = {
            "op_eqeq": ["&kp EQUAL", "&kp EQUAL"],
            "op_neq": ["&kp EXCL", "&kp EQUAL"],
            "op_lte": ["&kp LT", "&kp EQUAL"],
            "op_gte": ["&kp GT", "&kp EQUAL"],
            "op_arrow": ["&kp MINUS", "&kp GT"],
            "op_fatarrow": ["&kp EQUAL", "&kp GT"],
            "op_and": ["&kp AMPS", "&kp AMPS"],
            "op_or": ["&kp PIPE", "&kp PIPE"],
            "op_walrus": ["&kp COLON", "&kp EQUAL"],
            "op_pow": ["&kp ASTRK", "&kp ASTRK"],
            "op_floordiv": ["&kp FSLH", "&kp FSLH"],
            "ps_eq": ["&kp MINUS", "&kp E", "&kp Q"],
            "ps_ne": ["&kp MINUS", "&kp N", "&kp E"],
            "ps_lt": ["&kp MINUS", "&kp L", "&kp T"],
            "ps_le": ["&kp MINUS", "&kp L", "&kp E"],
            "ps_gt": ["&kp MINUS", "&kp G", "&kp T"],
            "ps_ge": ["&kp MINUS", "&kp G", "&kp E"],
            "op_sql_ne": ["&kp LT", "&kp GT"],
            "op_scope": ["&kp COLON", "&kp COLON"],
            "ps_current": ["&kp DLLR", "&kp UNDER"],
            "op_comment": ["&kp MINUS", "&kp MINUS"],
        }
        for name, sequence in expected_macros.items():
            self.assertEqual(verify_workflow.macro_bindings(text, name), sequence, name)
            body = verify_workflow.node_body(text, name)
            self.assertIn("wait-ms = <20>", body, name)
            self.assertIn("tap-ms = <20>", body, name)

        self.assertEqual(
            sym[1],
            ["&trans", "&op_eqeq", "&op_neq", "&op_lte", "&op_gte", "&op_arrow", "&trans", "&trans", "&op_fatarrow", "&op_and", "&op_or", "&op_walrus", "&op_pow", "&op_floordiv"],
        )
        self.assertEqual(
            sym[3],
            ["&trans", "&ps_eq", "&ps_ne", "&ps_lt", "&ps_le", "&ps_gt", "&trans", "&trans", "&ps_ge", "&op_sql_ne", "&op_scope", "&ps_current", "&op_comment", "&trans"],
        )

        for behavior in ("tlt", "num_caps"):
            body = verify_workflow.node_body(text, behavior)
            self.assertIn('flavor = "hold-preferred"', body)
            self.assertIn("tapping-term-ms = <170>", body)

    def test_host_adapters(self) -> None:
        verify_workflow.check_hammerspoon(ROOT / "host/hammerspoon-adv360.lua")
        verify_workflow.check_hyprland()
        verify_workflow.check_nvim(ROOT / "host/nvim-adv360.lua", "test Neovim")
        hyprland = (ROOT / "host/hyprland-adv360.lua").read_text()
        self.assertIn("local function shellQuote", hyprland)
        self.assertNotIn("%q", hyprland)
        self.assertFalse((ROOT / "host/aerospace.toml").exists(), "stale F21-F24 AeroSpace reference must not remain")

    def test_ci_requires_a_real_lua_syntax_parser(self) -> None:
        with (
            mock.patch.dict(os.environ, {"CI": "true"}),
            mock.patch.object(verify_workflow.shutil, "which", return_value=None),
        ):
            with self.assertRaisesRegex(AssertionError, "Lua syntax parser"):
                verify_workflow.check_lua_syntax()

    def test_karabiner_rule_is_device_scoped_and_complete(self) -> None:
        verify_workflow.check_karabiner(json.loads((ROOT / "host/karabiner-adv360.json").read_text()), "test")

    def test_action_resolution_is_argv_not_shell(self) -> None:
        host = adv360_action.host_name()
        command, _ = adv360_action.resolve_action("terminal", host)
        self.assertIsInstance(command, list)
        self.assertTrue(command)
        self.assertNotIn(";", command[0])

    def test_build_inputs_are_pinned(self) -> None:
        verify_workflow.check_build_and_docs()
        left_defconfig = (ROOT / "config/boards/arm/adv360/adv360_left_defconfig").read_text()
        self.assertNotIn("F13-F24", left_defconfig)

    def test_zmk_studio_left_half_contract(self) -> None:
        keymap = (ROOT / "config/adv360.keymap").read_text()
        config = (ROOT / "config/adv360.conf").read_text()
        build = (ROOT / "bin/build.sh").read_text()
        workflow = (ROOT / ".github/workflows/build.yml").read_text()
        board = (ROOT / "config/boards/arm/adv360/adv360.dtsi").read_text()
        layouts = (ROOT / "config/boards/arm/adv360/adv360-layouts.dtsi").read_text()
        readme = (ROOT / "README.md").read_text()
        agent_contract = (ROOT / "AGENTS.md").read_text()

        self.assertIn("#include <behaviors/studio_unlock.dtsi>", keymap)
        self.assertEqual(verify_workflow.layer_rows(keymap, "layer_sys")[1][9], "&studio_unlock")
        self.assertIn("CONFIG_ZMK_STUDIO=n", config, "right peripheral must keep Studio disabled")
        self.assertEqual(build.count("-S studio-rpc-usb-uart"), 1)
        self.assertEqual(build.count("-DCONFIG_ZMK_STUDIO=y"), 1)
        self.assertEqual(workflow.count("-S studio-rpc-usb-uart"), 1)
        self.assertEqual(workflow.count("-DCONFIG_ZMK_STUDIO=y"), 1)
        self.assertIn("zmk,physical-layout = &physical_layout0", board)
        self.assertIn('compatible = "zmk,physical-layout"', layouts)
        self.assertIn("keys", layouts)
        self.assertIn("ZMK Studio", readme)
        self.assertIn("SYS + U", readme)
        self.assertIn("Studio edits", agent_contract)
        self.assertNotIn("ZMK Studio remains disabled", agent_contract)

    def test_left_build_removes_same_fingerprint_right_artifact(self) -> None:
        build = (ROOT / "bin/build.sh").read_text()
        self.assertIn('rm -f "firmware/${prefix}-right.uf2"', build)

    def test_make_mounts_are_stable_under_dash_c(self) -> None:
        makefile = (ROOT / "Makefile").read_text()
        self.assertIn('"$(CURDIR)/firmware:/app/firmware', makefile)
        self.assertIn('"$(CURDIR)/config:/app/config:ro', makefile)
        self.assertIn("--untracked-files=normal", makefile)
        self.assertNotIn('"$(PWD)/', makefile)

    def test_docker_context_excludes_repo_noise(self) -> None:
        dockerignore = (ROOT / ".dockerignore").read_text()
        for entry in (".git", "firmware", "docs", "host", "tests", "assets"):
            self.assertIn(entry, dockerignore.splitlines())

    def test_firmware_fingerprint_covers_all_config_and_build_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bin").mkdir()
            (root / "config/boards").mkdir(parents=True)
            (root / "Dockerfile").write_text("FROM pinned\n")
            (root / "bin/build.sh").write_text("build\n")
            (root / "config/adv360.keymap").write_text("keymap-v1\n")
            (root / "config/boards/board.dts").write_text("board-v1\n")
            command = [sys.executable, str(ROOT / "scripts/firmware_fingerprint.py"), "--root", str(root)]
            first = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertRegex(first.stdout.strip(), r"^[0-9a-f]{12}$")
            (root / "config/boards/board.dts").write_text("board-v2\n")
            second = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertNotEqual(first.stdout, second.stdout)

        makefile = (ROOT / "Makefile").read_text()
        workflow = (ROOT / ".github/workflows/build.yml").read_text()
        self.assertIn("scripts/firmware_fingerprint.py", makefile)
        self.assertIn("scripts/firmware_fingerprint.py", workflow)

    def test_host_marker_install_is_idempotent(self) -> None:
        first = manage_host.upsert_block("before\n", "-- BEGIN", "-- END", "value")
        second = manage_host.upsert_block(first, "-- BEGIN", "-- END", "value")
        self.assertEqual(first, second)

    def test_host_installer_replaces_obsolete_karabiner_rule(self) -> None:
        data = {
            "profiles": [{
                "selected": True,
                "complex_modifications": {"rules": [
                    {"description": "ADV360 WM F21-F24 bridge for AeroSpace"},
                    {"description": "keep me"},
                ]},
            }],
        }
        result = manage_host.merged_karabiner(data)
        descriptions = [rule["description"] for rule in result["profiles"][0]["complex_modifications"]["rules"]]
        self.assertEqual(descriptions, ["ADV360 normalize F14/F15 for Hammerspoon", "keep me"])

    def test_host_rollback_rejects_backup_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            state_root = parent / "state"
            escape = parent / "escape"
            state_root.mkdir()
            escape.mkdir()
            with mock.patch.object(manage_host, "STATE_ROOT", state_root):
                with self.assertRaises(manage_host.InstallError):
                    manage_host.latest_state("../escape")

    def test_host_rollback_rejects_unmanaged_manifest_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            state_root = parent / "state"
            state = state_root / "20260731T120000+0200"
            state.mkdir(parents=True)
            outside = parent / "must-survive"
            outside.write_text("safe")
            manifest = {
                "schema": 1,
                "root": str(ROOT),
                "files": [{"path": str(outside), "existed": False, "backup": None}],
                "links": [],
            }
            (state / "manifest.json").write_text(json.dumps(manifest))
            with mock.patch.object(manage_host, "STATE_ROOT", state_root):
                with self.assertRaises(manage_host.InstallError):
                    manage_host.rollback(state.name)
            self.assertTrue(outside.exists())

    def test_host_rollback_rejects_symlinked_parent_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            managed_root = parent / "managed-root"
            outside = parent / "outside"
            state_root = parent / "state"
            state = state_root / "20260731T120000+0200"
            managed_root.mkdir()
            outside.mkdir()
            state.mkdir(parents=True)
            linked_parent = managed_root / "linked"
            linked_parent.symlink_to(outside, target_is_directory=True)
            target = linked_parent / "managed.lua"
            target.write_text("must-survive")
            backup = state / "file-0.backup"
            backup.write_text("attacker-data")
            manifest = {
                "schema": 1,
                "root": str(ROOT),
                "files": [{"path": str(target), "existed": True, "backup": str(backup)}],
                "links": [],
            }
            (state / "manifest.json").write_text(json.dumps(manifest))
            with (
                mock.patch.object(manage_host, "STATE_ROOT", state_root),
                mock.patch.object(manage_host, "managed_file_paths", return_value={target}),
                mock.patch.object(manage_host, "managed_root", return_value=managed_root),
            ):
                with self.assertRaises(manage_host.InstallError):
                    manage_host.rollback(state.name)
            self.assertEqual(target.read_text(), "must-survive")

    def test_host_rollback_restores_validated_managed_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            state_root = parent / "state"
            state = state_root / "20260731T120000+0200"
            state.mkdir(parents=True)
            target = parent / "managed.lua"
            target.write_text("new")
            backup = state / "file-0.backup"
            backup.write_text("old")
            manifest = {
                "schema": 1,
                "root": str(ROOT),
                "files": [{"path": str(target), "existed": True, "backup": str(backup)}],
                "links": [],
            }
            (state / "manifest.json").write_text(json.dumps(manifest))
            with (
                mock.patch.object(manage_host, "STATE_ROOT", state_root),
                mock.patch.object(manage_host, "managed_file_paths", return_value={target}),
                mock.patch.object(manage_host, "managed_root", return_value=parent.resolve()),
            ):
                self.assertEqual(manage_host.rollback(state.name), 0)
            self.assertEqual(target.read_text(), "old")

    def test_host_install_rolls_back_partial_write_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            state_root = parent / "state"
            action_link = parent / "bin/adv360-action"
            first = parent / "first.lua"
            second = parent / "second.lua"
            first.write_text("old-first")
            second.write_text("old-second")
            real_atomic_write = manage_host.atomic_write

            def fail_second(path: Path, text: str) -> None:
                if path == second:
                    raise OSError("simulated write failure")
                real_atomic_write(path, text)

            with (
                mock.patch.object(manage_host, "STATE_ROOT", state_root),
                mock.patch.object(manage_host, "ACTION_LINK", action_link),
                mock.patch.object(manage_host, "proposed_files", return_value={first: "new-first", second: "new-second"}),
                mock.patch.object(manage_host, "managed_file_paths", return_value={first, second}),
                mock.patch.object(manage_host, "managed_root", return_value=parent.resolve()),
                mock.patch.object(manage_host, "atomic_write", side_effect=fail_second),
            ):
                with self.assertRaises(manage_host.InstallError):
                    manage_host.install(dry_run=False)

            self.assertEqual(first.read_text(), "old-first")
            self.assertEqual(second.read_text(), "old-second")
            self.assertFalse(action_link.exists())


if __name__ == "__main__":
    unittest.main()
