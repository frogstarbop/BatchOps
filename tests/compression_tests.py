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

# settings presets to test with
high_res_preset = compression.CompressionSettings(
    max_file_size=800 * 1000,
    preferred_widths=[1920, 2560, 3840],
    min_height=1080,
    quality=80
)
med_res_preset = compression.CompressionSettings(
    max_file_size=600 * 1000,
    preferred_widths=[1280, 1920, 2560],
    min_height=720,
    quality=75
)
low_res_preset = compression.CompressionSettings(
    max_file_size=400 * 1000,
    preferred_widths=[1280, 1920],
    min_height=720,
    quality=70
)
presets = [high_res_preset, med_res_preset, low_res_preset]

# TODO: have test cases that make assertions
# example: self.assertEqual('foo'.upper(), 'FOO')

## @brief Tests compression on different filetypes
#
# This only checks that compression doesnt throw any errors
#
class TestCompressionDoesntCrash(unittest.TestCase):
    ## @brief Runs compression on an image and cleans up its used resources
    # @param self This test object
    # @param image_path The path of the image file to compress
    # @param settings The settings to apply when compressing
    def compress_image(self,
                       image_path: str,
                       settings: compression.CompressionSettings
                       ) -> None:
        print('loading file ' + image_path)
        image: PIL.Image.Image = PIL.Image.open(image_path)
        image.load()
        image_bytes: bytes = compression.process(image, settings)
        image.close()

    ## @brief Runs compression on every image in a folder recursively
    # @param self This test object
    # @param sub_directory The path containing the image files
    # @param settings The settings to apply when compressing
    def compress_folder(self,
                        sub_directory: str,
                        settings: compression.CompressionSettings
                        ) -> None:
        for file_name in os.listdir(sub_directory):
            file_path = os.path.join(sub_directory, file_name)
            if not os.path.isfile(file_path):
                # go in recursively
                self.compress_folder(file_path, settings)
                continue
            self.compress_image(file_path, settings)

    ## @brief Tests compression on input JPEG filetype
    # @param self This test object
    def test_compress_jpg(self):
        for preset in presets:
            self.compress_folder(images_jpg_dir, preset)

    ## @brief Tests compression on input PNG filetype
    # @param self This test object
    def test_compress_png(self):
        for preset in presets:
            self.compress_folder(images_png_dir, preset)

if __name__ == '__main__':
    unittest.main()