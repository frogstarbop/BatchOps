import unittest
import PIL.Image
import io

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
presets = [high_res_preset, med_res_preset, low_res_preset]

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
            print(f'----TESTING PRESET {preset.name}----')
            self.compress_folder(images_jpg_dir, preset)

    ## @brief Tests compression on input PNG filetype
    # @param self This test object
    def test_compress_png(self):
        for preset in presets:
            self.compress_folder(images_png_dir, preset)

if __name__ == '__main__':
    unittest.main()