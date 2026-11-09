import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/check.py'
SPEC = importlib.util.spec_from_file_location('toolkit_check', SCRIPT)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class DocumentationChecks(unittest.TestCase):
    def test_fenced_examples_and_external_links_are_not_local_dependencies(self):
        text = '[guide](docs/guide.md#section)\n```md\n[example](missing.md)\n```\n'
        text += '[reference]: <docs/with spaces.md>\n[external](https://example.invalid/a)\n[section](#here)'
        self.assertEqual(list(CHECK.local_targets(text)), ['docs/guide.md', 'docs/with spaces.md'])

    def test_source_file_links_fail_when_target_is_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            doc = root / 'README.md'
            doc.write_text('[guide](guide.md)')
            with self.assertRaises(ValueError):
                CHECK.check_links(root, [doc])
            (root / 'guide.md').write_text('Guide')
            CHECK.check_links(root, [doc])

    def test_existing_source_file_is_not_enough_for_installed_documentation(self):
        files = {'docs/infra-team-toolkit/standards/example.md': b'[tool](../scripts/tool.py)'}
        with self.assertRaises(ValueError):
            CHECK.check_installed_links(files)
        files['docs/infra-team-toolkit/scripts/tool.py'] = b'example'
        CHECK.check_installed_links(files)

    def test_optimization_flag_cannot_disable_required_structure_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary) / 'scripts/check.py'
            script.parent.mkdir()
            script.write_bytes(SCRIPT.read_bytes())
            result = subprocess.run([sys.executable, '-O', str(script)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Missing README.md', result.stderr)


if __name__ == '__main__':
    unittest.main()
