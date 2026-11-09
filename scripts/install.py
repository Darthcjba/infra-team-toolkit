#!/usr/bin/env python3
"""Install a committed toolkit without overwriting different consumer content."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
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


def application_root(target):
    if not target.is_dir():
        raise ValueError('Target must be an existing application directory')
    target = target.resolve()
    if Path(git(target, 'rev-parse', '--show-toplevel')).resolve() != target:
        raise ValueError('Target must be the Git working-tree root')
    return target


def destination(target, name):
    """Reject managed symlinks and non-directory parents before reading/writing."""
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or '\x00' in name:
        raise ValueError('Unsafe managed path refused')
    dest = target / name
    current = dest
    while current != target:
        if current.is_symlink():
            raise ValueError(f'Symlink refused: {name}')
        if current != dest and current.exists() and not current.is_dir():
            raise ValueError(f'Parent is not a directory: {name}')
        current = current.parent
    return dest


def managed_name(name):
    if not isinstance(name, str) or '\\' in name or '\x00' in name:
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or str(path) != name:
        return False
    return ((len(path.parts) > 1 and path.parts[0] == '.clinerules'
             and path.name.startswith('infra-team-toolkit-'))
            or name.startswith('.cline/skills/cjba-k8s-jsonnet/')
            or name.startswith('docs/infra-team-toolkit/standards/'))


def verify_installed(target):
    """Check recorded managed bytes independently of the current toolkit checkout."""
    target = application_root(target)
    manifest_path = destination(target, '.infra-team-toolkit.json')
    try:
        if not manifest_path.is_file():
            raise ValueError('Manifest is not a regular file')
        manifest = json.loads(manifest_path.read_text())
    except (OSError, ValueError):
        raise ValueError('Installed manifest is missing, unreadable or invalid JSON') from None
    if (not isinstance(manifest, dict)
            or not isinstance(manifest.get('revision'), str)
            or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', manifest['revision'])
            or not isinstance(manifest.get('files'), dict) or not manifest['files']):
        raise ValueError('Installed manifest must contain a Git revision and managed file checksums')
    # Validate all paths/checksums before reading any managed file.
    for name, checksum in manifest['files'].items():
        if not managed_name(name) or not isinstance(checksum, str) or not re.fullmatch(r'[0-9a-f]{64}', checksum):
            raise ValueError('Invalid managed path or checksum in installed manifest')
    errors = []
    for name, checksum in manifest['files'].items():
        try:
            dest = destination(target, name)
            if not dest.is_file():
                errors.append(f'Missing managed file: {name}')
            elif hashlib.sha256(dest.read_bytes()).hexdigest() != checksum:
                errors.append(f'Changed managed file: {name}')
        except (ValueError, OSError):
            errors.append(f'Unsafe or unreadable managed file: {name}')
    if errors:
        raise ValueError('\n'.join(errors))
    print(f'Verified installed {len(manifest["files"])} files; recorded revision {manifest["revision"]}')
    return manifest


def install(root, target, check=False, dry_run=False):
    if check and dry_run:
        raise ValueError('Choose check or dry-run, not both')
    target = application_root(target)
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
        try:
            dest = destination(target, name)
        except ValueError as error:
            errors.append(str(error))
            continue
        if dest.exists() and (not dest.is_file() or dest.read_bytes() != data):
            errors.append(f'Conflicting content: {name}')
        elif check and not dest.exists():
            errors.append(f'Missing: {name}')
    if errors:
        raise ValueError('\n'.join(errors))
    if dry_run:
        print(f'Planned {len(files)-1} managed files; revision {manifest["revision"]}; no files written')
        for name in files:
            print(f'{"Keep" if (target / name).exists() else "Create"}: {name}')
        return
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
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--check', action='store_true', help='compare with this clean toolkit revision')
    modes.add_argument('--dry-run', action='store_true', help='preflight and list planned files without writing')
    modes.add_argument('--verify-installed', action='store_true', help='verify the recorded manifest without requiring its toolkit checkout')
    args = parser.parse_args()
    try:
        if args.verify_installed:
            verify_installed(args.target)
        else:
            install(ROOT, args.target, args.check, args.dry_run)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'{exc}\n')

if __name__ == '__main__':
    main()
