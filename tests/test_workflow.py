#!/usr/bin/env python3

from __future__ import annotations

import csv
import importlib.util
import json
import os
import re
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
            "home_row_misfires": "0", "combo_misfires": "0", "aggressive_input_measured": "yes",
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

    def test_aggressive_input_measurement_fields_exist(self) -> None:
        for field in ("home_row_misfires", "combo_misfires", "aggressive_input_measured"):
            self.assertIn(field, field_test.FIELDS)

    def test_combo_misfire_blocks_strict_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            rows = [self.row(day, os_name="linux" if day % 2 == 0 else "macos") for day in range(1, 8)]
            rows[0]["combo_misfires"] = "1"
            field_test.write_rows(path, rows)
            result = self.run_report(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PENDING: zero combo misfires", result.stdout)

    def test_home_row_misfire_rate_blocks_strict_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            rows = [self.row(day, os_name="linux" if day % 2 == 0 else "macos") for day in range(1, 8)]
            rows[0]["home_row_misfires"] = "4"
            field_test.write_rows(path, rows)
            result = self.run_report(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PENDING: home-row mod misfires <= 0.5/hour", result.stdout)

    def test_previous_field_log_migrates_macro_errors_to_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            row = self.row(1)
            row.pop("macro_output_errors")
            row.pop("macro_output_measured")
            row.pop("home_row_misfires")
            row.pop("combo_misfires")
            row.pop("aggressive_input_measured")
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=field_test.PRE_MACRO_FIELDS)
                writer.writeheader()
                writer.writerow(row)
            original = path.read_text()
            field_test.ensure_log(path)
            migrated = field_test.read_rows(path)
            self.assertEqual(migrated[0]["macro_output_errors"], "0")
            self.assertEqual(migrated[0]["macro_output_measured"], "no")
            self.assertEqual(migrated[0]["home_row_misfires"], "0")
            self.assertEqual(migrated[0]["combo_misfires"], "0")
            self.assertEqual(migrated[0]["aggressive_input_measured"], "no")
            self.assertEqual(path.read_text().splitlines()[0].split(","), field_test.FIELDS)
            backup = path.with_name(path.name + ".pre-migration.bak")
            self.assertEqual(backup.read_text(), original)

    def test_invalid_legacy_log_is_not_modified_during_migration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            row = self.row(1)
            for field in ("home_row_misfires", "combo_misfires", "aggressive_input_measured"):
                row.pop(field)
            row["minutes"] = "invalid"
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=field_test.PRE_AGGRESSIVE_FIELDS)
                writer.writeheader()
                writer.writerow(row)
            original = path.read_text()
            with self.assertRaises(field_test.LogError):
                field_test.ensure_log(path)
            self.assertEqual(path.read_text(), original)
            self.assertFalse(path.with_name(path.name + ".pre-migration.bak").exists())

    def test_migration_does_not_reuse_or_overwrite_stale_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            row = self.row(1)
            for field in ("home_row_misfires", "combo_misfires", "aggressive_input_measured"):
                row.pop(field)
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=field_test.PRE_AGGRESSIVE_FIELDS)
                writer.writeheader()
                writer.writerow(row)
            original = path.read_bytes()
            stale = path.with_name(path.name + ".pre-migration.bak")
            stale.write_bytes(b"stale-backup")
            field_test.ensure_log(path)
            self.assertEqual(stale.read_bytes(), b"stale-backup")
            numbered = path.with_name(path.name + ".pre-migration.bak.1")
            self.assertEqual(numbered.read_bytes(), original)

    def test_migration_skips_symlinked_backup_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "log.csv"
            row = self.row(1)
            for field in ("home_row_misfires", "combo_misfires", "aggressive_input_measured"):
                row.pop(field)
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=field_test.PRE_AGGRESSIVE_FIELDS)
                writer.writeheader()
                writer.writerow(row)
            original = path.read_bytes()
            victim = root / "victim"
            victim.write_bytes(b"must-survive")
            occupied = path.with_name(path.name + ".pre-migration.bak")
            occupied.symlink_to(victim)
            field_test.ensure_log(path)
            self.assertTrue(occupied.is_symlink())
            self.assertEqual(victim.read_bytes(), b"must-survive")
            self.assertEqual(path.with_name(path.name + ".pre-migration.bak.1").read_bytes(), original)

    def test_pre_macro_field_sessions_cannot_pass_strict_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            rows = []
            for day in range(1, 8):
                row = self.row(day, os_name="linux" if day % 2 == 0 else "macos")
                row.pop("macro_output_errors")
                row.pop("macro_output_measured")
                row.pop("home_row_misfires")
                row.pop("combo_misfires")
                row.pop("aggressive_input_measured")
                rows.append(row)
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=field_test.PRE_MACRO_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            result = self.run_report(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PENDING: macro output measured in every session", result.stdout)

    def test_pre_aggressive_sessions_cannot_pass_strict_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "log.csv"
            rows = []
            for day in range(1, 8):
                row = self.row(day, os_name="linux" if day % 2 == 0 else "macos")
                for field in ("home_row_misfires", "combo_misfires", "aggressive_input_measured"):
                    row.pop(field)
                rows.append(row)
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=field_test.PRE_AGGRESSIVE_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            result = self.run_report(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PENDING: aggressive input measured in every session", result.stdout)

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

    def test_global_brackets_match_documented_workspace_cycle(self) -> None:
        keymap = (ROOT / "config/adv360.keymap").read_text()
        global_layer = verify_workflow.layer_rows(keymap, "layer_global")
        self.assertEqual(global_layer[4][1], "&kp LC(F17)", "GLOBAL + [ must select previous workspace")
        self.assertEqual(global_layer[4][2], "&kp LC(F18)", "GLOBAL + ] must select next workspace")
        protocol = (ROOT / "host/PROTOCOL.md").read_text()
        self.assertIn("GLOBAL + [ / ]", protocol)

    def test_keymap_semantics(self) -> None:
        verify_workflow.check_keymap()

    def test_six_layer_no_dead_key_architecture(self) -> None:
        text = (ROOT / "config/adv360.keymap").read_text()
        expected = {
            "BASE": "default_layer",
            "NAV": "layer_nav",
            "SYM": "layer_sym",
            "NUM": "layer_num",
            "GLOBAL": "layer_global",
            "SYS": "layer_sys",
        }
        for index, (name, node) in enumerate(expected.items()):
            self.assertIn(f"#define {name}", text)
            self.assertRegex(text, rf"#define\s+{name}\s+{index}\b")
            rows = verify_workflow.layer_rows(text, node)
            bindings = [binding for row in rows for binding in row]
            self.assertEqual(len(bindings), 76, name)
            self.assertNotIn("&none", bindings, f"{name} contains a dead key")
        for removed in ("CODE", "EDIT", "MOUSE", "MEDIA"):
            self.assertNotRegex(text, rf"(?m)^#define\s+{removed}\b")

    def test_production_home_row_and_thumb_contract(self) -> None:
        text = (ROOT / "config/adv360.keymap").read_text()
        base = verify_workflow.layer_rows(text, "default_layer")
        self.assertEqual(
            base[2],
            [
                "&kp ESC", "&hml LGUI A", "&hml LALT S", "&hml LCTRL D", "&hml LSHFT F", "&kp G",
                "&kp LALT", "&kp LCTRL", "&kp LGUI", "&kp RGUI", "&kp RCTRL", "&kp RALT",
                "&kp H", "&hmr RSHFT J", "&hmr RCTRL K", "&hmr RALT L", "&hmr RGUI SEMI", "&kp SQT",
            ],
        )
        base_flat = [binding for row in base for binding in row]
        for binding in (
            "&tlt_fast NAV ESC", "&tlt_fast SYM TAB", "&num_caps NUM 0",
            "&tlt_fast GLOBAL LA(F13)",
        ):
            self.assertEqual(base_flat.count(binding), 1, binding)
        for binding in ("&kp BSPC", "&kp DEL", "&kp ENTER", "&kp SPACE"):
            self.assertEqual(base_flat.count(binding), 1, binding)
        self.assertNotIn("&tlt_safe", text)

        own_layer_activation_positions = {
            "layer_nav": (3, 6), "layer_sym": (3, 7),
            "layer_num": (4, 7), "layer_global": (4, 8),
        }
        for node, (row, column) in own_layer_activation_positions.items():
            self.assertEqual(verify_workflow.layer_rows(text, node)[row][column], "&trans", node)

        for behavior in ("hml", "hmr"):
            body = verify_workflow.node_body(text, behavior)
            for token in (
                'flavor = "balanced"', "tapping-term-ms = <180>", "quick-tap-ms = <150>",
                "require-prior-idle-ms = <120>", "hold-trigger-on-release",
            ):
                self.assertIn(token, body, f"{behavior}: {token}")

        clean = verify_workflow.uncomment(text)
        combo_nodes = re.findall(r"\b(combo_[a-z0-9_]+)\s*\{(.*?)\};", clean, re.S)
        typing_combos = [(name, body) for name, body in combo_nodes if name not in {"combo_bt_clear", "combo_bootloader"}]
        self.assertEqual(len(typing_combos), 1)
        combo_map = dict(typing_combos)
        self.assertIn("key-positions = <15 16>", combo_map["combo_esc"], "Esc must avoid the frequent A+S bigram")
        self.assertIn("require-prior-idle-ms = <80>", combo_map["combo_esc"])
        for name, body in typing_combos:
            self.assertIn("timeout-ms = <35>", body, name)
            self.assertIn("layers = <BASE>", body, name)
            self.assertNotRegex(body, r"bindings\s*=.*\b(?:LG|LC|LA)\(", f"{name} is OS-specific")

        config = (ROOT / "config/adv360.conf").read_text()
        self.assertNotIn("CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY", config)
        self.assertNotIn("&tog", text)

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
        clean = verify_workflow.uncomment(text)
        for name, sequence in expected_macros.items():
            self.assertEqual(verify_workflow.macro_bindings(text, name), sequence, name)
            body = verify_workflow.node_body(text, name)
            self.assertIn("wait-ms = <20>", body, name)
            self.assertIn("tap-ms = <20>", body, name)
            self.assertEqual(len(re.findall(rf"&{name}\b", clean)), 1, name)

        self.assertEqual(
            sym[1],
            ["&trans", "&trans", "&op_lte", "&op_gte", "&op_arrow", "&op_fatarrow", "&trans", "&trans", "&op_and", "&op_or", "&op_walrus", "&op_pow", "&op_floordiv", "&op_scope"],
        )
        self.assertEqual(
            sym[3],
            ["&kp LSHFT", "&ps_eq", "&ps_ne", "&ps_lt", "&ps_le", "&ps_gt", "&trans", "&trans", "&ps_ge", "&op_sql_ne", "&ps_current", "&op_comment", "&kp LT", "&kp RSHFT"],
        )
        self.assertEqual(sym[4][5:7], ["&op_eqeq", "&op_neq"], "SYM Backspace/Delete must own the prime equality macros")
        self.assertEqual(sym[4][9:11], ["&trans", "&trans"], "SYM Enter/Space must remain plain passthrough keys")

        fast = verify_workflow.node_body(text, "tlt_fast")
        self.assertIn('flavor = "hold-preferred"', fast)
        self.assertIn("tapping-term-ms = <170>", fast)
        self.assertNotIn("tlt_safe:", text)

    def test_num_layer_has_vscode_debug_cluster_and_numpad(self) -> None:
        num = verify_workflow.layer_rows((ROOT / "config/adv360.keymap").read_text(), "layer_num")
        self.assertEqual(num[2][1:6], ["&kp F5", "&kp F9", "&kp F10", "&kp F11", "&kp F12"])
        self.assertEqual(num[2][12:18], ["&kp KP_MINUS", "&kp KP_N4", "&kp KP_N5", "&kp KP_N6", "&kp KP_PLUS", "&kp KP_MULTIPLY"])

    def test_nav_editor_panes_use_unambiguous_f21_f24_carriers(self) -> None:
        keymap = (ROOT / "config/adv360.keymap").read_text()
        nav = verify_workflow.layer_rows(keymap, "layer_nav")
        self.assertEqual(nav[1][8:12], ["&kp F21", "&kp F22", "&kp F23", "&kp F24"])
        self.assertEqual(
            nav[4][11:15],
            ["&msc SCRL_LEFT", "&msc SCRL_DOWN", "&msc SCRL_UP", "&msc SCRL_RIGHT"],
            "physical arrow cluster must retain keyboard scrolling",
        )
        self.assertNotIn("&mkp MCLK", " ".join(binding for row in nav for binding in row))

        nvim = (ROOT / "host/nvim-adv360.lua").read_text()
        for mode in ("n", "i", "t"):
            for number in range(21, 25):
                self.assertIn(f"vim.keymap.set('{mode}', '<F{number}>'", nvim)
        self.assertNotIn("<C-;>", nvim, "terminal-ambiguous Ctrl+; must be retired")

        vscode_path = ROOT / "host/vscode-adv360.json"
        self.assertTrue(vscode_path.is_file())
        self.assertEqual(
            json.loads(vscode_path.read_text()),
            [
                {"key": "f21", "command": "workbench.action.focusLeftGroup"},
                {"key": "f22", "command": "workbench.action.focusBelowGroup"},
                {"key": "f23", "command": "workbench.action.focusAboveGroup"},
                {"key": "f24", "command": "workbench.action.focusRightGroup"},
            ],
        )

    def test_active_vscode_verifier_allows_unrelated_custom_bindings(self) -> None:
        canonical = json.loads((ROOT / "host/vscode-adv360.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "keybindings.json"
            path.write_text(json.dumps([
                {"key": "cmd+k cmd+s", "command": "workbench.action.openGlobalKeybindings"},
                *canonical,
            ]))
            verify_workflow.check_vscode(path, "customized VS Code", allow_extra=True)

            path.write_text(json.dumps([
                *canonical,
                {"key": "f21", "command": "workbench.action.closeActiveEditor"},
            ]))
            with self.assertRaises(AssertionError):
                verify_workflow.check_vscode(path, "conflicting VS Code", allow_extra=True)

    def test_readme_matches_physical_macro_and_editor_carrier_positions(self) -> None:
        readme = (ROOT / "README.md").read_text()
        for token in (
            "SYM + Backspace    ==", "SYM + Delete       !=",
            "Tab and Q pass through", "NAV + Y/U/I/O", "pane left/down/up/right",
            "F21/F22/F23/F24", "NAV + physical arrows", "scroll left/down/up/right",
        ):
            self.assertIn(token, readme)
        self.assertNotIn("Q ==    W !=", readme)

    def test_host_adapters(self) -> None:
        verify_workflow.check_aerospace(ROOT / "host/macos/aerospace.toml", "repository AeroSpace")
        verify_workflow.check_hyprland()
        verify_workflow.check_nvim(ROOT / "host/nvim-adv360.lua", "test Neovim")
        verify_workflow.check_vscode(ROOT / "host/vscode-adv360.json", "test VS Code")
        hyprland = (ROOT / "host/hyprland-adv360.lua").read_text()
        self.assertIn("local function shellQuote", hyprland)
        self.assertNotIn("%q", hyprland)
        self.assertFalse((ROOT / "host/hammerspoon-adv360.lua").exists(), "Hammerspoon must not remain a supported macOS owner")
        self.assertFalse((ROOT / "host/karabiner-adv360.json").exists(), "Hammerspoon-only Karabiner normalization must be retired")

    def test_ci_requires_a_real_lua_syntax_parser(self) -> None:
        with (
            mock.patch.dict(os.environ, {"CI": "true"}),
            mock.patch.object(verify_workflow.shutil, "which", return_value=None),
        ):
            with self.assertRaisesRegex(AssertionError, "Lua syntax parser"):
                verify_workflow.check_lua_syntax()

    def test_active_macos_verifier_requires_aerospace_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            hammerspoon = home / ".hammerspoon/init.lua"
            karabiner = home / ".config/karabiner/karabiner.json"
            aerospace = home / ".config/aerospace/aerospace.toml"
            nvim = home / ".config/nvim/init.lua"
            vscode = home / "Library/Application Support/Code/User/keybindings.json"
            action_link = home / ".local/bin/adv360-action"
            for path in (hammerspoon, karabiner, aerospace, nvim, vscode, action_link):
                path.parent.mkdir(parents=True, exist_ok=True)
            hammerspoon.write_text("-- unrelated Hammerspoon config\n")
            karabiner.write_text(json.dumps({"profiles": [{"selected": True, "complex_modifications": {"rules": [{"description": "keep me"}]}}]}))
            source = (ROOT / "host/macos/aerospace.toml").read_text()
            aerospace.write_text(source.replace("__ADV360_ACTION__", str(action_link)))
            nvim.write_text("dofile('" + str(ROOT / "host/nvim-adv360.lua") + "')\n")
            vscode.write_text((ROOT / "host/vscode-adv360.json").read_text())
            action_link.symlink_to(ROOT / "scripts/adv360_action.py")
            calls: list[list[str]] = []

            def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess:
                calls.append(command)
                if command == ["/usr/bin/pgrep", "-x", "Hammerspoon"]:
                    return subprocess.CompletedProcess(command, 0, stdout="123\n", stderr="")
                if command[0] == "/opt/homebrew/bin/hs":
                    return subprocess.CompletedProcess(command, 0, stdout="[]\n", stderr="")
                if command[1:] == ["list-workspaces", "--all"]:
                    output = "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n"
                elif command[1:] == ["list-monitors"]:
                    output = "1 | PG32UCDM\n2 | P34WD-40\n"
                elif command[1:] == ["list-workspaces", "--monitor", "1"]:
                    output = "1\n2\n3\n4\n5\n"
                elif command[1:] == ["list-workspaces", "--monitor", "2"]:
                    output = "6\n7\n8\n9\n10\n"
                elif command[1:] == ["config", "--get", "mode.main.binding", "--json"]:
                    loaded = verify_workflow.aerospace_bindings(aerospace.read_text(), "test active")
                    loaded = {key: value.replace("exec-and-forget ", "exec-and-forget  ") for key, value in loaded.items()}
                    output = json.dumps(loaded)
                elif command[1:] == ["config", "--config-path"]:
                    output = str(aerospace) + "\n"
                else:
                    output = "ok\n"
                return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

            def fake_which(command: str):
                return {"aerospace": "/opt/homebrew/bin/aerospace", "hs": "/opt/homebrew/bin/hs"}.get(command)

            with (
                mock.patch.object(verify_workflow.Path, "home", return_value=home),
                mock.patch.object(verify_workflow.shutil, "which", side_effect=fake_which),
                mock.patch.object(verify_workflow.subprocess, "run", side_effect=fake_run),
            ):
                verify_workflow.check_active_macos()
            self.assertIn(["/opt/homebrew/bin/aerospace", "reload-config"], calls)
            self.assertIn(["/opt/homebrew/bin/aerospace", "config", "--config-path"], calls)
            self.assertIn(["/opt/homebrew/bin/aerospace", "config", "--get", "mode.main.binding", "--json"], calls)
            self.assertIn(["/opt/homebrew/bin/aerospace", "list-workspaces", "--monitor", "1"], calls)
            self.assertIn(["/opt/homebrew/bin/aerospace", "list-workspaces", "--monitor", "2"], calls)
            self.assertIn(["/opt/homebrew/bin/hs", "-c", verify_workflow.HAMMERSPOON_CARRIER_QUERY], calls)

    def test_hammerspoon_runtime_registry_rejects_f13_f20(self) -> None:
        self.assertIn("h.idx", verify_workflow.HAMMERSPOON_CARRIER_QUERY)
        result = subprocess.CompletedProcess(["hs"], 0, stdout=json.dumps(["⌘F13", "⌃⇧F20"]), stderr="")
        with mock.patch.object(verify_workflow.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(AssertionError, "F13-F20"):
                verify_workflow.check_hammerspoon_runtime("/opt/homebrew/bin/hs")

    def test_selected_karabiner_profile_rejects_unknown_carrier_rewrite(self) -> None:
        data = {
            "profiles": [{
                "selected": True,
                "simple_modifications": [{"from": {"key_code": "f15"}, "to": [{"key_code": "a"}]}],
                "complex_modifications": {"rules": [{
                    "description": "custom unrelated-looking rule",
                    "manipulators": [{
                        "type": "basic",
                        "from": {"simultaneous": [{"key_code": "f16"}, {"key_code": "j"}]},
                        "to": [{"key_code": "k"}],
                    }],
                }]},
            }],
        }
        with self.assertRaisesRegex(AssertionError, "Karabiner.*F13-F20"):
            verify_workflow.check_karabiner_carrier_conflicts(data, "test Karabiner")

    def test_action_resolution_is_argv_not_shell(self) -> None:
        host = adv360_action.host_name()
        command, _ = adv360_action.resolve_action("terminal", host)
        self.assertIsInstance(command, list)
        self.assertTrue(command)
        self.assertNotIn(";", command[0])

    def test_macos_launcher_uses_working_spotlight_shortcut_argv(self) -> None:
        command, fallback = adv360_action.resolve_action("launcher", "macos")
        self.assertEqual(command, [
            "/usr/bin/osascript",
            "-e",
            'tell application "System Events" to key code 49 using {command down}',
        ])
        self.assertIsNone(fallback)

    def test_build_inputs_are_pinned(self) -> None:
        verify_workflow.check_build_and_docs()
        left_defconfig = (ROOT / "config/boards/arm/adv360/adv360_left_defconfig").read_text()
        self.assertNotIn("F13-F24", left_defconfig)
        readme = (ROOT / "README.md").read_text()
        protocol = (ROOT / "host/PROTOCOL.md").read_text()
        agent_contract = (ROOT / "AGENTS.md").read_text()
        field_test = (ROOT / "docs/7-day-field-test.md").read_text()
        self.assertIn("AeroSpace owns macOS", readme)
        self.assertIn("AeroSpace owns macOS", protocol)
        self.assertIn("AeroSpace", agent_contract)
        self.assertNotIn("exercise Hammerspoon", field_test)
        self.assertTrue((ROOT / "scripts/manage_host.py").is_file())
        self.assertIn("python3 scripts/manage_host.py plan", readme)
        self.assertIn("python3 scripts/manage_host.py install", readme)
        self.assertNotIn("scripts/propose_host_changes.py", readme)
        self.assertNotIn("scripts/apply_host_changes.py", readme)

    def test_production_redesign_documentation_contract(self) -> None:
        readme = (ROOT / "README.md").read_text()
        agent_contract = (ROOT / "AGENTS.md").read_text()
        field_test = (ROOT / "docs/7-day-field-test.md").read_text()
        optimization_log = (ROOT / "docs/optimization-log.md").read_text()
        for token in (
            "Six-layer architecture", "only BASE typing combo", "35 ms", "home-row modifiers",
            "Backspace, Delete, Enter, and Space remain plain", "no `&none`",
        ):
            self.assertIn(token, readme)
        for token in ("six layers", "G and H are active", "one BASE typing combo", "zero combo misfires"):
            self.assertIn(token, agent_contract)
        for token in ("--home-row-misfires", "--combo-misfires", "zero combo misfires"):
            self.assertIn(token, field_test)
        self.assertIn("six-layer production candidate", optimization_log)

    def test_zmk_studio_left_half_contract(self) -> None:
        keymap = (ROOT / "config/adv360.keymap").read_text()
        config = (ROOT / "config/adv360.conf").read_text()
        build = (ROOT / "bin/build.sh").read_text()
        workflow = (ROOT / ".github/workflows/build.yml").read_text()
        board = (ROOT / "config/boards/arm/adv360/adv360.dtsi").read_text()
        layouts = (ROOT / "config/boards/arm/adv360/adv360-layouts.dtsi").read_text()
        left_defconfig = (ROOT / "config/boards/arm/adv360/adv360_left_defconfig").read_text()
        right_defconfig = (ROOT / "config/boards/arm/adv360/adv360_right_defconfig").read_text()
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
        self.assertIn("CONFIG_ZMK_USB=y", left_defconfig)
        self.assertNotIn("CONFIG_ZMK_USB=y", right_defconfig, "split peripheral must not request unsupported USB")
        self.assertIn("CONFIG_ZMK_RGB_UNDERGLOW_AUTO_OFF_IDLE=y", right_defconfig)
        self.assertNotIn("CONFIG_ZMK_RGB_UNDERGLOW_AUTO_OFF_IDLE=n", right_defconfig)
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

    def test_host_marker_install_rejects_duplicate_or_unbalanced_markers(self) -> None:
        with self.assertRaises(manage_host.InstallError):
            manage_host.upsert_block("-- BEGIN\na\n-- BEGIN\nb\n-- END\n", "-- BEGIN", "-- END", "value")
        with self.assertRaises(manage_host.InstallError):
            manage_host.upsert_block("-- BEGIN\na\n", "-- BEGIN", "-- END", "value")

    def test_host_installer_removes_hammerspoon_adapter_block(self) -> None:
        text = "before\n-- BEGIN ADV360 HOST ADAPTER\nold\n-- END ADV360 HOST ADAPTER\nafter\n"
        result = manage_host.remove_block(text, manage_host.HAMMER_START, manage_host.HAMMER_END)
        self.assertEqual(result, "before\nafter\n")

    def test_host_installer_renders_aerospace_action_path(self) -> None:
        rendered = manage_host.rendered_aerospace()
        self.assertNotIn("__ADV360_ACTION__", rendered)
        self.assertEqual(rendered.count(str(manage_host.ACTION_LINK)), 8)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "aerospace.toml"
            path.write_text(rendered)
            verify_workflow.check_aerospace(path, "rendered AeroSpace")

    def test_darwin_host_proposal_installs_aerospace_and_retires_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            hammerspoon = home / ".hammerspoon/init.lua"
            karabiner = home / ".config/karabiner/karabiner.json"
            aerospace = home / ".config/aerospace/aerospace.toml"
            nvim = home / ".config/nvim/init.lua"
            for path in (hammerspoon, karabiner, aerospace, nvim):
                path.parent.mkdir(parents=True, exist_ok=True)
            hammerspoon.write_text("before\n-- BEGIN ADV360 HOST ADAPTER\nold\n-- END ADV360 HOST ADAPTER\nafter\n")
            karabiner.write_text(json.dumps({"profiles": [{"selected": True, "complex_modifications": {"rules": [
                {"description": "ADV360 normalize F14/F15 for Hammerspoon"},
                {"description": "keep me"},
            ]}}]}))
            aerospace.write_text("start-at-login = false\n")
            nvim.write_text("")
            with (
                mock.patch.object(manage_host.Path, "home", return_value=home),
                mock.patch.object(manage_host.platform, "system", return_value="Darwin"),
            ):
                proposed = manage_host.proposed_files()
            self.assertNotIn("ADV360 HOST ADAPTER", proposed[hammerspoon])
            self.assertNotIn("normalize F14/F15", proposed[karabiner])
            self.assertEqual(proposed[aerospace], manage_host.rendered_aerospace())
            self.assertIn("nvim-adv360.lua", proposed[nvim])

    def test_darwin_host_proposal_rejects_legacy_aerospace_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            legacy = home / ".aerospace.toml"
            legacy.write_text("config-version = 2\n")
            with (
                mock.patch.object(manage_host.Path, "home", return_value=home),
                mock.patch.object(manage_host.platform, "system", return_value="Darwin"),
            ):
                with self.assertRaisesRegex(manage_host.InstallError, "ambiguous"):
                    manage_host.proposed_files()

    def test_host_installer_removes_obsolete_karabiner_protocol_rules(self) -> None:
        data = {
            "profiles": [
                {
                    "selected": True,
                    "complex_modifications": {"rules": [
                        {"description": "ADV360 WM F21-F24 bridge for AeroSpace"},
                        {"description": "ADV360 normalize F14/F15 for Hammerspoon"},
                        {"description": "keep me"},
                    ]},
                },
                {
                    "selected": False,
                    "complex_modifications": {"rules": [
                        {"description": "ADV360 normalize F14/F15 for Hammerspoon"},
                        {"description": "keep inactive profile rule"},
                    ]},
                },
            ],
        }
        result = manage_host.cleaned_karabiner(data)
        descriptions = [
            [rule["description"] for rule in profile["complex_modifications"]["rules"]]
            for profile in result["profiles"]
        ]
        self.assertEqual(descriptions, [["keep me"], ["keep inactive profile rule"]])

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

    def test_host_rollback_rejects_special_target_before_any_restore(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            state_root = parent / "state"
            state = state_root / "20260731T120000+0200"
            state.mkdir(parents=True)
            first = parent / "first.lua"
            first.write_text("current-first")
            special = parent / "special-target"
            special.mkdir()
            first_backup = state / "file-0.backup"
            second_backup = state / "file-1.backup"
            first_backup.write_text("old-first")
            second_backup.write_text("old-second")
            manifest = {
                "schema": 1,
                "root": str(ROOT),
                "files": [
                    {"path": str(first), "existed": True, "backup": str(first_backup)},
                    {"path": str(special), "existed": True, "backup": str(second_backup)},
                ],
                "links": [],
            }
            (state / "manifest.json").write_text(json.dumps(manifest))
            with (
                mock.patch.object(manage_host, "STATE_ROOT", state_root),
                mock.patch.object(manage_host, "managed_file_paths", return_value={first, special}),
                mock.patch.object(manage_host, "managed_root", return_value=parent.resolve()),
            ):
                with self.assertRaisesRegex(manage_host.InstallError, "regular file"):
                    manage_host.rollback(state.name)
            self.assertEqual(first.read_text(), "current-first")
            self.assertTrue(special.is_dir())
            self.assertEqual(list(special.iterdir()), [])

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

    def test_atomic_write_ignores_predictable_temp_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            target = parent / "managed.toml"
            victim = parent / "victim"
            victim.write_text("must-survive")
            predictable = target.with_name(target.name + ".adv360.tmp")
            predictable.symlink_to(victim)
            manage_host.atomic_write(target, "new-config")
            self.assertEqual(target.read_text(), "new-config")
            self.assertEqual(victim.read_text(), "must-survive")
            self.assertTrue(predictable.is_symlink())

    def test_atomic_write_preserves_existing_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "private-config"
            target.write_text("old")
            target.chmod(0o6750)
            before = target.stat()
            manage_host.atomic_write(target, "new")
            after = target.stat()
            self.assertEqual(target.read_text(), "new")
            self.assertEqual(after.st_mode & 0o7777, 0o6750)
            self.assertEqual((after.st_uid, after.st_gid), (before.st_uid, before.st_gid))
            created = Path(directory) / "new-private-config"
            manage_host.atomic_write(created, "created")
            self.assertEqual(created.stat().st_mode & 0o777, 0o600)

    def test_host_install_rejects_symlinked_managed_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            state_root = parent / "state"
            action_link = parent / "bin/adv360-action"
            outside = parent / "outside.toml"
            outside.write_text("new")
            target = parent / "aerospace.toml"
            target.symlink_to(outside)
            with (
                mock.patch.object(manage_host, "STATE_ROOT", state_root),
                mock.patch.object(manage_host, "ACTION_LINK", action_link),
                mock.patch.object(manage_host, "proposed_files", return_value={target: "new"}),
                mock.patch.object(manage_host, "managed_file_paths", return_value={target}),
                mock.patch.object(manage_host, "managed_root", return_value=parent.resolve()),
            ):
                with self.assertRaisesRegex(manage_host.InstallError, "symlink"):
                    manage_host.install(dry_run=False)
            self.assertTrue(target.is_symlink())
            self.assertEqual(outside.read_text(), "new")

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
