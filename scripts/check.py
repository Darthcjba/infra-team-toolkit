#!/usr/bin/env python3
"""Offline structural checks; does not render application manifests."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
required = ['README.md', 'GOVERNANCE.md', 'CONTRIBUTING.md', '.github/CODEOWNERS',
            'standards/app-infrastructure.md', 'templates/AGENTS.md', 'scripts/install.py']
for name in required:
    assert (root / name).is_file(), f'Missing {name}'
assert (root / '.github/CODEOWNERS').read_text().strip() == '* @Darthcjba'
for folder in ['rules', 'skills', 'standards', 'templates', 'scripts']:
    assert any((root / folder).iterdir()), f'Empty directory: {folder}'
for skill in (root / 'skills').glob('*/SKILL.md'):
    text = skill.read_text()
    assert text.startswith('---\n'), f'Missing frontmatter: {skill}'
    header = text.split('---', 2)[1]
    assert re.search(r'^name:\s*' + re.escape(skill.parent.name) + r'\s*$', header, re.M)
    assert re.search(r'^description:\s*\S', header, re.M)
    for ref in re.findall(r'`(references/[^`]+)`', text):
        assert (skill.parent / ref).is_file(), f'Missing reference: {ref}'
print('Toolkit structure, sole code owner and skill references verified.')
