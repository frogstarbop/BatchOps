import unittest
from PIL.Image import Image, open as image_open
from io import BytesIO

from test_lib import test_preset_list, images_jpg_dir, images_png_dir, images_compression_failure
import image_compression as compression


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
                       image: Image,
                       settings: compression.CompressionSettings
                       ) -> None:
        print()
        result_data: bytes = compression.process(image, settings)
        stream: BytesIO = BytesIO(result_data)
        result_img: Image = image_open(stream, 'r')
        stream.close()

        self.assertGreaterEqual(image.width, result_img.width)
        self.assertGreaterEqual(image.height, result_img.height)
        self.assertAlmostEqual(image.width / image.height, result_img.width / result_img.height, 3)
        self.assertGreaterEqual(settings.max_file_size, len(result_data))


    ## @brief Check that compression on an image fails
    # @param self This test object
    # @param image_path The relative filepath to the image and its filename
    # @param settings The compression settings to apply
    def compress_image_fail(self,
                            image: Image,
                            settings: compression.CompressionSettings
                            ) -> None:
        # expect compression to raise an error, fail the test if not
        with self.assertRaises(compression.CompressionError):
            image_bytes: bytes = compression.process(image, settings)

        print('threw as expected')
        image.close()

    ## @brief Tests compression on input JPEG filetype
    # @param self Thisst object
    def test_compress_jpg(self):
        test_preset_list(images_jpg_dir, presets, self.compress_image)

    ## @brief Tests compression on input PNG filetype
    # @param self This test object
    def test_compress_png(self):
        test_preset_list(images_png_dir, presets, self.compress_image)

    ## @brief Tests that compression with impossible settings on large files does fail
    # @param self This test object
    def test_failure(self):
        test_preset_list(images_compression_failure, fail_presets, self.compress_image_fail)

# allow to run tests individually
if __name__ == '__main__':
    unittest.main()