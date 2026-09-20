import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin'))
from manage_host import apply_files, jsonc, merge_aerospace, merge_keybindings, native_settings, restore


class HostManagementTests(unittest.TestCase):
    def test_aerospace_merge_preserves_environment_and_custom_bindings(self):
        original = '''start-at-login = true
[gaps]
inner.horizontal = 8
[mode.main.binding]
f13 = ['workspace 9', 'balance-sizes']
alt-z = 'focus left'
[mode.resize.binding]
h = 'resize width -10'
'''
        fragment = '''[mode.main.binding]
f13 = 'workspace 1'
alt-f13 = 'exec-and-forget open -a "Ghostty"'
'''
        merged = merge_aerospace(original, fragment)
        parsed = tomllib.loads(merged)
        self.assertEqual(parsed['gaps']['inner']['horizontal'], 8)
        self.assertEqual(parsed['mode']['main']['binding']['alt-z'], 'focus left')
        self.assertEqual(parsed['mode']['resize']['binding']['h'], 'resize width -10')
        self.assertEqual(merge_aerospace(merged, fragment), merged)

    def test_aerospace_multiline_binding(self):
        original = "[mode.main.binding]\nf13 = [\n'workspace 9',\n'balance-sizes'\n]\nalt-z = 'focus left'\n"
        result = merge_aerospace(original, "[mode.main.binding]\nf13 = 'workspace 1'\n")
        self.assertEqual(tomllib.loads(result)['mode']['main']['binding'], {'f13': 'workspace 1', 'alt-z': 'focus left'})

    def test_jsonc_preserves_urls_and_string_punctuation(self):
        self.assertEqual(jsonc('{"url":"https://example.test/a/*b", // comment\n"s":",}",}'),
                         {'url': 'https://example.test/a/*b', 's': ',}'})

    def test_keybindings_keep_custom_and_replace_reserved_bank(self):
        existing = '[{"key":"f21","command":"old"},{"key":"cmd+k x","command":"mine"}]'
        desired = [{'key': 'f21', 'command': 'new'}]
        result = merge_keybindings(existing, desired)
        self.assertEqual(json.loads(result)[0]['command'], 'mine')
        self.assertEqual(merge_keybindings(result, desired), result)

    def test_settings_preserve_development_options(self):
        original = '{"python.analysis.typeCheckingMode":"basic","vscode-neovim.compositeTimeout":200,"extensions.experimental.affinity":{"other":1,"asvetliakov.vscode-neovim":1}}'
        result = json.loads(native_settings(original))
        self.assertEqual(result['python.analysis.typeCheckingMode'], 'basic')
        self.assertEqual(result['extensions.experimental.affinity'], {'other': 1})
        self.assertNotIn('vscode-neovim.compositeTimeout', result)

    def test_backup_restore_and_idempotent_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / 'existing'; existing.write_bytes(b'old')
            added = root / 'added'
            files = {existing: b'new', added: b'created'}
            backup = apply_files(files, root / 'backups')
            self.assertIsNone(apply_files(files, root / 'backups'))
            restore(backup)
            self.assertEqual(existing.read_bytes(), b'old')
            self.assertFalse(added.exists())

    def test_restore_refuses_later_user_edits_before_touching_any_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); first = root / 'first'; second = root / 'second'
            first.write_bytes(b'old'); second.write_bytes(b'old')
            backup = apply_files({first: b'new', second: b'new'}, root / 'backups')
            second.write_bytes(b'user edit')
            with self.assertRaisesRegex(ValueError, 'later edits'):
                restore(backup)
            self.assertEqual(first.read_bytes(), b'new')
            self.assertEqual(second.read_bytes(), b'user edit')
