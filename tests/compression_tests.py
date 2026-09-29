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

# constants
images_src_dir: str = 'images'
images_jpg_dir: str = os.path.join(images_src_dir, 'jpeg')
images_png_dir: str = os.path.join(images_src_dir, 'png')

# TODO: have test cases that make assertions
# example: self.assertEqual('foo'.upper(), 'FOO')

## @brief Tests compression on different filetypes
#
# This only checks that compression doesnt throw any errors
#
class TestCompressionDoesntCrash(unittest.TestCase):
    ## @brief Tests that compression doesnt crash on an image
    def compress_image(self, image_path: str) -> None:
        print('loading file ' + image_path)
        image: PIL.Image.Image = PIL.Image.open(image_path)
        image.load()
        image_bytes: bytes = compression.compress(image)
        image.close()

    ## @brief Runs compression on every image in a folder recursively
    def compress_folder(self, sub_directory: str) -> None:
        for file_name in os.listdir(sub_directory):
            file_path = os.path.join(sub_directory, file_name)
            if not os.path.isfile(file_path):
                # go in recursively
                self.compress_folder(file_path)
                continue
            self.compress_image(file_path)

    ## @brief Tests compression on input JPEG filetype
    def test_compress_jpg(self):
        self.compress_folder(images_jpg_dir)

    ## @brief Tests compression on input PNG filetype
    def test_compress_png(self):
        self.compress_folder(images_png_dir)

if __name__ == '__main__':
    unittest.main()