import json
import re
import tempfile
import unittest
from pathlib import Path

from release.pages import build


class CachePolicyTests(unittest.TestCase):
    def test_only_generated_assets_use_immutable_browser_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            (destination / 'assets').mkdir()
            (destination / 'assets/index-ABCD1234.css').write_text('')
            build(destination)
            rules = json.loads((destination / 'vercel.json').read_text())['headers']

        def headers(path):
            result = {}
            for rule in rules:
                if re.fullmatch(rule['source'], path):
                    result.update({h['key'].lower(): h['value'] for h in rule['headers']})
            return result

        for path in ('/assets/index-ABCD1234.js', '/assets/index-ABCD1234.css', '/assets/Font-ABCD1234.woff2'):
            with self.subTest(path=path):
                self.assertEqual(headers(path).get('cache-control'), 'public, max-age=31536000, immutable')
                self.assertIn("frame-ancestors 'none'", headers(path)['content-security-policy'])
        for path in ('/', '/index.html', '/recording.json', '/ledger.json', '/filing-agent-source.zip'):
            with self.subTest(path=path):
                self.assertNotIn('cache-control', headers(path))


if __name__ == '__main__':
    unittest.main()
