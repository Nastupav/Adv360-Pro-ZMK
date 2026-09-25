#!/usr/bin/env python3
"""Preview/apply/restore the macOS integration; export an importable VS Code profile.

Uses Python 3.11+. Never rewrites VS Code's profile registry or original profile.
Create Advantage360 Native by copying the original in VS Code, or import the
generated .code-profile, before applying. Backups are local, mode 0700/0600.
"""
from __future__ import annotations

import argparse
import base64
import difflib
import hashlib
import json
import os
import re
import subprocess
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = "Advantage360 Native"


def jsonc(text):
    # Match strings before comments so URLs and comment-looking string values survive.
    text = re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/',
                  lambda m: m[0] if m[0].startswith('"') else '', text, flags=re.S)
    text = re.sub(r'"(?:\\.|[^"\\])*"|,\s*(?=[}\]])',
                  lambda m: m[0] if m[0].startswith('"') else '', text)
    return json.loads(text)


def dump(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def read(path):
    return path.read_bytes() if path.exists() else None


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd, temporary = tempfile.mkstemp(prefix=".adv360-", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def merge_aerospace(existing, fragment):
    """Replace only protocol-owned keys in main.binding; retain all other text."""
    wanted = tomllib.loads(fragment)["mode"]["main"]["binding"]
    parsed = tomllib.loads(existing)
    if "main" not in parsed.get("mode", {}):
        merged = existing.rstrip() + "\n\n" + fragment
        tomllib.loads(merged)
        return merged
    headers = list(re.finditer(r'^\s*\[[^\n]+\]\s*$', existing, re.M))
    target = next((m for m in headers if m[0].strip() == "[mode.main.binding]"), None)
    if target is None:
        raise ValueError("Use an explicit [mode.main.binding] table before applying")
    end = next((m.start() for m in headers if m.start() > target.start()), len(existing))
    section = existing[target.end():end]
    # A parser determines ownership. Replace complete TOML assignments, including
    # multiline arrays/strings, by finding the next assignment boundary.
    assignments = list(re.finditer(r'^\s*((?:[\w-]+)|(?:"[^"\n]+")|(?:\x27[^\x27\n]+\x27))\s*=', section, re.M))
    spans = []
    for i, match in enumerate(assignments):
        key = match[1].strip('"\x27')
        if key in wanted:
            stop = assignments[i+1].start() if i+1 < len(assignments) else len(section)
            spans.append((match.start(), stop))
    # Preserve comments outside replaced assignments; unrelated assignments remain verbatim.
    for start, stop in reversed(spans):
        section = section[:start] + section[stop:]
    owned = "\n# Advantage360 managed desktop signals\n" + "\n".join(
        f"{key} = {json.dumps(value, ensure_ascii=False)}" for key, value in wanted.items()) + "\n"
    section = section.replace("# Advantage360 managed desktop signals\n", "")
    merged = existing[:target.end()].rstrip() + "\n" + section.strip() + owned + "\n" + existing[end:].lstrip("\n")
    result = tomllib.loads(merged)
    # Prove that semantic values outside the owned keys did not change.
    for document in (parsed, result):
        table = document.get("mode", {}).get("main", {}).get("binding", {})
        for key in wanted:
            table.pop(key, None)
    if parsed != result:
        raise ValueError("Refusing merge: unrelated AeroSpace settings would change")
    return merged


def merge_keybindings(existing, desired):
    old = jsonc(existing) if existing.strip() else []
    identities = {(b['key'], b.get('when')) for b in desired}
    editor_key = re.compile(r'(?:^|\+)f2[1-4]$', re.I)
    retained = [b for b in old if not editor_key.search(b.get('key', ''))
                and (b.get('key'), b.get('when')) not in identities]
    return dump(retained + desired)


def native_settings(text):
    settings = jsonc(text)
    settings = {key: value for key, value in settings.items() if not key.startswith('vscode-neovim.')}
    affinity = settings.get('extensions.experimental.affinity', {})
    affinity.pop('asvetliakov.vscode-neovim', None)
    return dump(settings)


def code_user(home):
    return home / 'Library/Application Support/Code/User'


def native_profile(home):
    user = code_user(home)
    storage = json.loads((user / 'globalStorage/storage.json').read_text())
    matches = [p for p in storage.get('userDataProfiles', []) if p['name'] == PROFILE]
    if len(matches) != 1:
        raise ValueError(f'Create/import exactly one "{PROFILE}" profile in VS Code first')
    p = matches[0]
    if p.get('useDefaultFlags', {}).get('keybindings') or p.get('useDefaultFlags', {}).get('settings'):
        raise ValueError('The native profile must COPY settings/shortcuts, not share Default contents')
    location = p['location']
    if not isinstance(location, str) or Path(location).name != location:
        raise ValueError('Unsupported VS Code profile location')
    return user / 'profiles' / location


def export_profile(home, destination):
    user = code_user(home)
    bindings = merge_keybindings((user / 'keybindings.json').read_text() if (user / 'keybindings.json').exists() else '[]',
                                json.loads((ROOT / 'host/vscode/keybindings.json').read_text()))
    settings = native_settings((user / 'settings.json').read_text() if (user / 'settings.json').exists() else '{}')
    extensions = json.loads((home / '.vscode/extensions/extensions.json').read_text())
    exported = [{'identifier': e['identifier'], 'version': e['version'],
                 'disabled': e['identifier']['id'] == 'asvetliakov.vscode-neovim'} for e in extensions]
    profile = {'name': PROFILE, 'settings': dump({'settings': settings}),
               'keybindings': dump({'keybindings': bindings, 'platform': 1}),
               'extensions': dump(exported)}
    snippets = user / 'snippets'
    if snippets.exists():
        profile['snippets'] = dump({'snippets': {str(p.relative_to(snippets)): p.read_text()
                                               for p in snippets.rglob('*') if p.is_file()}})
    if (user / 'tasks.json').exists():
        profile['tasks'] = dump({'tasks': (user / 'tasks.json').read_text()})
    atomic_write(destination, dump(profile).encode())
    print(f'Importable profile: {destination}')


def planned_files(home):
    candidates = [home / '.aerospace.toml', home / '.config/aerospace/aerospace.toml']
    existing = [p for p in candidates if p.exists()]
    if len(existing) > 1:
        raise ValueError('Both AeroSpace config locations exist; resolve the duplicate first')
    target = existing[0] if existing else candidates[1]
    initial = target.read_text() if target.exists() else (ROOT / 'host/macos/aerospace.preamble.toml').read_text()
    aerospace = merge_aerospace(initial, (ROOT / 'host/macos/aerospace.toml').read_text())
    profile = native_profile(home)
    desired = json.loads((ROOT / 'host/vscode/keybindings.json').read_text())
    return {
        target: aerospace.encode(),
        home / '.local/share/adv360/spotlight-clipboard.applescript': (ROOT / 'host/macos/spotlight-clipboard.applescript').read_bytes(),
        profile / 'keybindings.json': merge_keybindings((profile / 'keybindings.json').read_text() if (profile / 'keybindings.json').exists() else '[]', desired).encode(),
        profile / 'settings.json': native_settings((profile / 'settings.json').read_text()).encode(),
    }


def keyboard_navigation():
    result = subprocess.run(['defaults', 'read', '-g', 'AppleKeyboardUIMode'], capture_output=True, text=True)
    if result.returncode:
        return None
    return int(result.stdout.strip())


def set_keyboard_navigation(value):
    args = ['defaults', 'delete', '-g', 'AppleKeyboardUIMode'] if value is None else [
        'defaults', 'write', '-g', 'AppleKeyboardUIMode', '-int', str(value)]
    subprocess.run(args, check=True)


def apply_files(files, backup_root, preference=None, update_preference=False):
    changed = {path: data for path, data in files.items() if read(path) != data}
    if not changed and not update_preference:
        print('Already current; no files or settings changed')
        return None
    backup = backup_root / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backup.mkdir(parents=True, mode=0o700)
    entries = []
    for path, data in changed.items():
        before = read(path)
        entries.append({'path': str(path), 'before': base64.b64encode(before).decode() if before is not None else None,
                        'after_sha256': digest(data), 'before_sha256': digest(before)})
    manifest = {'files': entries, 'keyboard_navigation_changed': update_preference,
                'keyboard_navigation_before': preference, 'keyboard_navigation_after': (preference or 0) | 2}
    atomic_write(backup / 'manifest.json', dump(manifest).encode())
    try:
        for path, data in changed.items():
            if digest(read(path)) != next(e['before_sha256'] for e in entries if e['path'] == str(path)):
                raise ValueError(f'File changed during apply: {path}')
            atomic_write(path, data)
        if update_preference:
            set_keyboard_navigation(manifest['keyboard_navigation_after'])
    except Exception:
        # Roll back only files that still contain our exact output.
        for e in entries:
            path = Path(e['path'])
            if digest(read(path)) == e['after_sha256']:
                if e['before'] is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, base64.b64decode(e['before']))
        raise
    print(f'Applied {len(changed)} files. Restore with: python3 bin/manage_host.py restore {backup}')
    return backup


def restore(backup):
    manifest = json.loads((backup / 'manifest.json').read_text())
    for e in manifest['files']:
        if digest(read(Path(e['path']))) != e['after_sha256']:
            raise ValueError(f"Refusing restore over later edits: {e['path']}")
    if manifest['keyboard_navigation_changed'] and keyboard_navigation() != manifest['keyboard_navigation_after']:
        raise ValueError('Keyboard Navigation changed since installation; restore it manually')
    for e in manifest['files']:
        path = Path(e['path'])
        if e['before'] is None:
            path.unlink()
        else:
            atomic_write(path, base64.b64decode(e['before']))
    if manifest['keyboard_navigation_changed']:
        set_keyboard_navigation(manifest['keyboard_navigation_before'])
    print('Restored backed-up files and Keyboard Navigation; reload AeroSpace/VS Code')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['preview', 'apply', 'restore', 'export-profile'])
    parser.add_argument('path', nargs='?', type=Path)
    args = parser.parse_args()
    home = Path.home()
    if args.action == 'restore':
        if args.path is None:
            parser.error('restore needs a backup directory')
        return restore(args.path)
    if args.action == 'export-profile':
        return export_profile(home, args.path or ROOT / 'firmware/Advantage360 Native.code-profile')
    files = planned_files(home)
    before = keyboard_navigation()
    if args.action == 'preview':
        for path, data in files.items():
            print(''.join(difflib.unified_diff((read(path) or b'').decode().splitlines(True),
                        data.decode().splitlines(True), fromfile=str(path), tofile=str(path))), end='')
        print(f'Keyboard Navigation: {before!r} -> {(before or 0) | 2}')
    else:
        apply_files(files, home / '.local/state/adv360/backups', before, before is None or not before & 2)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
