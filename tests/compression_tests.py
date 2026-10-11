import unittest
import PIL.Image
import io
from collections.abc import Callable

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
images_failues_dir: str = os.path.join(images_src_dir, 'compression_specific')

# settings presets to test with
high_res_preset = compression.CompressionSettings(
    name='high',
    max_file_size=800 * 1000,
    preferred_widths=[1920, 2560, 3840],
    min_height=1080,
    quality=80
)
med_res_preset = compression.CompressionSettings(
    name='med',
    max_file_size=400 * 1000,
    preferred_widths=[1280, 1920, 2560],
    min_height=720,
    quality=75
)
low_res_preset = compression.CompressionSettings(
    name='low',
    max_file_size=300 * 1000,
    preferred_widths=[1024, 1280, 1920],
    min_height=720,
    quality=70
)
# basically impossible settings
tiny_res_preset = compression.CompressionSettings(
    name='tiny',
    max_file_size= 100 * 1000,
    preferred_widths=[1280, 1920],
    min_height=720,
    quality=80
)
tall_res_preset = compression.CompressionSettings(
    name='tall',
    max_file_size= 100 * 1000,
    preferred_widths=[1280, 1920],
    min_height=7200,
    quality=80
)
wide_res_preset = compression.CompressionSettings(
    name='wide',
    max_file_size= 100 * 1000,
    preferred_widths=[10000],
    min_height=7200,
    quality=80
)
presets = [high_res_preset, med_res_preset, low_res_preset]
fail_presets = [tiny_res_preset, tall_res_preset, wide_res_preset]
## @brief Tests compression on different filetypes
#
# This does several checks on the images:
#   1. image is only getting smaller in dimensions
#   2. image maintains approximate aspect ratio
#   3. image is under max file size
#   4. (implicitly) compression doesnt throw errors
class TestCompression(unittest.TestCase):
    ## @brief Runs compression on an image and cleans up its used resources
    # @param self This test object
    # @param image_path The path of the image file to compress
    # @param settings The settings to apply when compressing
    def compress_image(self,
                       image_path: str,
                       settings: compression.CompressionSettings
                       ) -> None:
        print()
        print('loading file ' + image_path)
        image: PIL.Image.Image = PIL.Image.open(image_path)
        image.load()
        image_bytes: bytes = compression.process(image, settings)
        stream: io.BytesIO = io.BytesIO(image_bytes)
        result_img = PIL.Image.open(stream, 'r')

        self.assertGreaterEqual(image.width, result_img.width)
        self.assertGreaterEqual(image.height, result_img.height)
        self.assertAlmostEqual(image.width / image.height, result_img.width / result_img.height, 3)
        self.assertGreaterEqual(settings.max_file_size, len(image_bytes))

        image.close()

    ## @brief Check that compression on an image fails
    # @param self This test object
    # @param image_path The relative filepath to the image and its filename
    # @param settings The compression settings to apply
    def compress_image_fail(self,
                            image_path: str,
                            settings: compression.CompressionSettings
                            ) -> None:
        print()
        print('loading file ' + image_path)
        image: PIL.Image.Image = PIL.Image.open(image_path)
        image.load()

        # expect compression to raise an error, fail the test if not
        with self.assertRaises(compression.CompressionError):
            image_bytes: bytes = compression.process(image, settings)

        print('threw as expected')
        image.close()

    ## @brief Runs compression on every image in a folder recursively
    # @param self This test object
    # @param sub_directory The path containing the image files
    # @param settings The settings to apply when compressing
    def compress_folder(self,
                        sub_directory: str,
                        settings: compression.CompressionSettings,
                        operation: Callable[[str, compression.CompressionSettings], None]
                        ) -> None:
        for file_name in os.listdir(sub_directory):
            file_path = os.path.join(sub_directory, file_name)
            if not os.path.isfile(file_path):
                # go in recursively
                self.compress_folder(file_path, settings, operation)
                continue
            operation(file_path, settings)

    ## @brief Tests compression on input JPEG filetype
    # @param self This test object
    def test_compress_jpg(self):
        for preset in presets:
            print(f'----TESTING PRESET {preset.name}----')
            self.compress_folder(images_jpg_dir, preset, self.compress_image)

    ## @brief Tests compression on input PNG filetype
    # @param self This test object
    def test_compress_png(self):
        for preset in presets:
            self.compress_folder(images_png_dir, preset, self.compress_image)

    ## @brief Tests that compression with impossible settings on large files does fail
    # @param self This test object
    def test_failure(self):
        for preset in fail_presets:
            print(f'----TESTING FAIL-PRESET {preset.name}----')
            self.compress_folder(images_failues_dir, preset, self.compress_image_fail)
if __name__ == '__main__':
    unittest.main()