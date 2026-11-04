import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath

from release.source_bundle import ROOT, bundle


class SourceBundleTests(unittest.TestCase):
    def test_relative_stylesheet_assets_are_present_in_source_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'source.zip'
            bundle(destination)
            with zipfile.ZipFile(destination) as archive:
                stylesheet = PurePosixPath('slice/web/src/styles.css')
                references = re.findall(r'url\(["\']?(\./[^"\')]+)', archive.read(str(stylesheet)).decode())
                self.assertTrue(references, 'Exercise actual local stylesheet dependencies')
                manifest = json.loads(archive.read('SOURCE-MANIFEST.json'))
                for reference in references:
                    name = str(stylesheet.parent / reference)
                    with self.subTest(asset=name):
                        self.assertIn(name, archive.namelist())
                        self.assertIn(name, manifest)
                        self.assertEqual(archive.read(name), (ROOT / name).read_bytes())


if __name__ == '__main__':
    unittest.main()
