#!/usr/bin/env python3
"""Install a committed toolkit without overwriting different consumer content."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()

def payload(root):
    files = {}
    for source, destination in [('rules', '.clinerules'), ('skills/cjba-k8s-jsonnet', '.cline/skills/cjba-k8s-jsonnet'), ('standards', 'docs/infra-team-toolkit/standards')]:
        base = root / source
        for f in sorted(base.rglob('*')):
            if f.is_symlink():
                raise ValueError(f'Source symlink refused: {f}')
            if f.is_file():
                relative = f.relative_to(base)
                if source == 'rules':
                    relative = relative.with_name('infra-team-toolkit-' + relative.name)
                files[str(Path(destination) / relative)] = f.read_bytes()
    if not files:
        raise ValueError('No toolkit payload found')
    return files

def install(root, target, check=False):
    if not target.is_dir():
        raise ValueError('Target must be an existing application directory')
    target = target.resolve()
    if Path(git(target, 'rev-parse', '--show-toplevel')).resolve() != target:
        raise ValueError('Target must be the Git working-tree root')
    if target == root.resolve():
        raise ValueError('Use an application checkout, not the toolkit itself')
    if git(root, 'status', '--porcelain'):
        raise ValueError('Commit toolkit changes before installing or checking')
    files = payload(root)
    manifest = {'revision': git(root, 'rev-parse', 'HEAD'), 'files': {
        name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    files['.infra-team-toolkit.json'] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    errors = []
    for name, data in files.items():
        dest = target / name
        if any(p.is_symlink() for p in [dest, *dest.parents] if p != target.parent):
            errors.append(f'Symlink refused: {name}')
        elif any(p.exists() and not p.is_dir() for p in dest.parents if p != target.parent):
            errors.append(f'Parent is not a directory: {name}')
        elif dest.exists() and (not dest.is_file() or dest.read_bytes() != data):
            errors.append(f'Conflicting content: {name}')
        elif check and not dest.exists():
            errors.append(f'Missing: {name}')
    if errors:
        raise ValueError('\n'.join(errors))
    if not check:
        for name, data in files.items():
            dest = target / name
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
    print(f'{"Verified" if check else "Installed"} {len(files)-1} files; revision {manifest["revision"]}')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        install(ROOT, args.target, args.check)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'{exc}\n')

if __name__ == '__main__':
    main()
