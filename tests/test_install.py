import importlib.util
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
