import unittest
import subprocess
import sys
from image_convert_cli import cli

class SmokeTests(unittest.TestCase):
    def test_help(self):
        r = subprocess.run([sys.executable, '-m', 'image_convert_cli', '--help'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('usage:', r.stdout)

import tempfile
from pathlib import Path
from PIL import Image
class ImageTests(unittest.TestCase):
    def test_alpha_jpeg_resize(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'in.png'; dst=Path(d)/'out.jpg'
            Image.new('RGBA',(20,10),(255,0,0,0)).save(src)
            cli.convert(src,dst,80,10)
            with Image.open(dst) as im:
                self.assertEqual(im.size,(10,5)); self.assertGreater(im.getpixel((0,0))[0],240)
            with self.assertRaises(ValueError): cli.convert(src,dst)

