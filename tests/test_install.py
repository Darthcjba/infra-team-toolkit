import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'scripts/install.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.source, self.target = base / 'toolkit', base / 'app'
        for p in [self.source, self.target]:
            p.mkdir()
            subprocess.run(['git', 'init', '-q', str(p)], check=True)
        for name in ['rules/example.md', 'skills/cjba-k8s-jsonnet/SKILL.md', 'standards/app.md']:
            p = self.source / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('example\n')
        subprocess.run(['git', '-C', str(self.source), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.source), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture'], check=True)
    def test_install_repeat_and_drift(self):
        module.install(self.source, self.target)
        module.install(self.source, self.target)
        module.install(self.source, self.target, check=True)
        (self.target / '.clinerules/infra-team-toolkit-example.md').write_text('local edit')
        with self.assertRaises(ValueError):
            module.install(self.source, self.target, check=True)
    def test_conflict_has_no_partial_writes(self):
        p = self.target / 'docs/infra-team-toolkit/standards/app.md'
        p.parent.mkdir(parents=True)
        p.write_text('keep me')
        with self.assertRaises(ValueError):
            module.install(self.source, self.target)
        self.assertFalse((self.target / '.clinerules').exists())
        self.assertEqual(p.read_text(), 'keep me')
    def test_symlink_refused(self):
        (self.target / '.clinerules').symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            module.install(self.source, self.target)
        self.assertFalse((self.target / '.infra-team-toolkit.json').exists())
    def test_dirty_source_refused(self):
        (self.source / 'rules/example.md').write_text('uncommitted')
        with self.assertRaises(ValueError):
            module.install(self.source, self.target)

    def test_preview_preflights_without_creating_any_payload(self):
        module.install(self.source, self.target, dry_run=True)
        self.assertEqual([p.name for p in self.target.iterdir()], ['.git'])
        p = self.target / 'docs/infra-team-toolkit/standards/app.md'
        p.parent.mkdir(parents=True)
        p.write_text('local content')
        with self.assertRaises(ValueError):
            module.install(self.source, self.target, dry_run=True)
        self.assertFalse((self.target / '.clinerules').exists())
        self.assertEqual(p.read_text(), 'local content')

    def test_recorded_verification_is_independent_of_current_source(self):
        module.install(self.source, self.target)
        (self.source / 'rules/example.md').write_text('new uncommitted toolkit')
        before = {str(p): p.read_bytes() for p in self.target.rglob('*') if p.is_file()}
        manifest = module.verify_installed(self.target)
        self.assertEqual(manifest['revision'], module.git(self.source, 'rev-parse', 'HEAD'))
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.target.rglob('*') if p.is_file()})
        with self.assertRaises(ValueError):
            module.install(self.source, self.target, check=True)

    def test_recorded_verification_rejects_missing_and_changed_files(self):
        module.install(self.source, self.target)
        (self.target / '.clinerules/infra-team-toolkit-example.md').unlink()
        (self.target / 'docs/infra-team-toolkit/standards/app.md').write_text('local edit')
        with self.assertRaises(ValueError) as error:
            module.verify_installed(self.target)
        self.assertIn('Missing managed file', str(error.exception))
        self.assertIn('Changed managed file', str(error.exception))

    def test_recorded_verification_rejects_manifest_and_managed_symlinks(self):
        module.install(self.source, self.target)
        managed = self.target / '.clinerules/infra-team-toolkit-example.md'
        managed.unlink()
        managed.symlink_to(self.source / 'rules/example.md')
        with self.assertRaises(ValueError):
            module.verify_installed(self.target)
        manifest = self.target / '.infra-team-toolkit.json'
        outside = self.source / 'saved-manifest.json'
        outside.write_bytes(manifest.read_bytes())
        manifest.unlink()
        manifest.symlink_to(outside)
        with self.assertRaises(ValueError):
            module.verify_installed(self.target)

    def test_recorded_verification_rejects_escape_and_unmanaged_paths(self):
        module.install(self.source, self.target)
        manifest_path = self.target / '.infra-team-toolkit.json'
        original = json.loads(manifest_path.read_text())
        for name in ['../outside', '/tmp/outside', '.git/config', 'docs/../outside',
                     '.cline\\skills\\outside', 'unmanaged.txt']:
            with self.subTest(name=name):
                manifest = {**original, 'files': {name: '0' * 64}}
                manifest_path.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    module.verify_installed(self.target)

    def test_recorded_verification_rejects_invalid_manifest_shapes(self):
        module.install(self.source, self.target)
        manifest_path = self.target / '.infra-team-toolkit.json'
        for value in [[], {}, {'revision': 'not-a-revision', 'files': {'x': '0' * 64}},
                      {'revision': '0' * 40, 'files': {}},
                      {'revision': '0' * 40, 'files': {'.clinerules/infra-team-toolkit-x.md': 'bad'}}]:
            with self.subTest(value=value):
                manifest_path.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    module.verify_installed(self.target)

    def test_non_directory_parent_preflight_has_no_partial_writes(self):
        (self.target / 'docs').write_text('application-owned file')
        with self.assertRaises(ValueError):
            module.install(self.source, self.target)
        self.assertFalse((self.target / '.clinerules').exists())
        self.assertEqual((self.target / 'docs').read_text(), 'application-owned file')

    def test_invalid_manifest_json_does_not_echo_content(self):
        manifest_path = self.target / '.infra-team-toolkit.json'
        manifest_path.write_text('private-invalid-manifest')
        with self.assertRaises(ValueError) as error:
            module.verify_installed(self.target)
        self.assertNotIn('private-invalid-manifest', str(error.exception))
        manifest_path.unlink()
        manifest_path.mkdir()
        with self.assertRaises(ValueError):
            module.verify_installed(self.target)
