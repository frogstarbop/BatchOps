import unittest
import PIL.Image

# this makes the module to test importable
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
outer_dir = os.path.dirname(current_dir)
sys.path.append(outer_dir)

# the module to test
import compression

image_subdir_name: str = 'images'

class TestStringMethods(unittest.TestCase):
    def test_compress_jpg(self):
        # self.assertEqual('foo'.upper(), 'FOO')
        image_filename: str = 'DSC09877.jpg'
        image_path: str = os.path.join(image_subdir_name, image_filename)
        print('loading file ' + image_path)
        image: PIL.Image.Image = PIL.Image.open(image_path)
        image.load()
        image_bytes: bytes = compression.compress(image)
        image.close()
    def test_compress_png(self):
            # self.assertEqual('foo'.upper(), 'FOO')
            image_filename: str = 'HIGH.png'
            image_path: str = os.path.join(image_subdir_name, image_filename)
            print('loading file ' + image_path)
            image: PIL.Image.Image = PIL.Image.open(image_path)
            image.load()
            image_bytes: bytes = compression.compress(image)
            image.close()
if __name__ == '__main__':
    unittest.main()