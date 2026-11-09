#!/usr/bin/env python3
"""Offline structure and authored documentation checks; does not render apps."""
import importlib.util
from pathlib import Path
import posixpath
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ['README.md', 'GOVERNANCE.md', 'CONTRIBUTING.md', '.github/CODEOWNERS',
            'standards/app-infrastructure.md', 'templates/AGENTS.md', 'scripts/install.py']


def local_targets(text):
    """Read authored inline/reference file links, excluding fenced examples."""
    lines, fence = [], None
    for line in text.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line)
    prose = '\n'.join(lines)
    targets = re.findall(r'\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)', prose)
    targets += re.findall(r'^\[[^\]]+\]:\s*(<[^>]+>|\S+)', prose, re.M)
    for target in targets:
        parsed = urlsplit(target.strip('<>'))
        if not parsed.scheme and not parsed.netloc and parsed.path:
            yield unquote(parsed.path)


def check_links(root, paths):
    errors = []
    for path in paths:
        for target in local_targets(path.read_text()):
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                errors.append(f'Broken local link in {path.relative_to(root)}: {target}')
    if errors:
        raise ValueError('\n'.join(errors))


def check_installed_links(files):
    errors = []
    for name, data in files.items():
        if not (name.startswith('docs/infra-team-toolkit/standards/') and name.endswith('.md')):
            continue
        for target in local_targets(data.decode()):
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
            if resolved not in files and not any(p.startswith(resolved.rstrip('/') + '/') for p in files):
                errors.append(f'Link target is not installed with {name}: {target}')
    if errors:
        raise ValueError('\n'.join(errors))


def check(root):
    for name in REQUIRED:
        if not (root / name).is_file():
            raise ValueError(f'Missing {name}')
    if (root / '.github/CODEOWNERS').read_text().strip() != '* @Darthcjba':
        raise ValueError('Unexpected toolkit code owner')
    for folder in ['rules', 'skills', 'standards', 'templates', 'scripts']:
        if not (root / folder).is_dir() or not any((root / folder).iterdir()):
            raise ValueError(f'Empty or missing directory: {folder}')
    for skill in (root / 'skills').glob('*/SKILL.md'):
        text = skill.read_text()
        if not text.startswith('---\n') or len(text.split('---', 2)) != 3:
            raise ValueError(f'Missing skill frontmatter: {skill.relative_to(root)}')
        header = text.split('---', 2)[1]
        if not re.search(r'^name:\s*' + re.escape(skill.parent.name) + r'\s*$', header, re.M):
            raise ValueError(f'Invalid skill name: {skill.relative_to(root)}')
        if not re.search(r'^description:\s*\S', header, re.M):
            raise ValueError(f'Missing skill description: {skill.relative_to(root)}')
        for ref in re.findall(r'`(references/[^`]+)`', text):
            if not (skill.parent / ref).is_file():
                raise ValueError(f'Missing skill reference: {ref}')
    # Preserve the supplied skill archive; validate authored repo docs separately.
    paths = list(root.glob('*.md'))
    for folder in ['docs', 'rules', 'standards', 'templates', 'scripts']:
        paths.extend((root / folder).rglob('*.md'))
    paths.append(root / 'skills/README.md')
    check_links(root, paths)
    spec = importlib.util.spec_from_file_location('toolkit_installer', root / 'scripts/install.py')
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    check_installed_links(installer.payload(root))


def main():
    try:
        check(ROOT)
    except (OSError, ValueError) as error:
        print('Toolkit check failed: ' + str(error), file=sys.stderr)
        return 1
    print('Toolkit structure, owner, skill references and authored source/installed file links verified.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
