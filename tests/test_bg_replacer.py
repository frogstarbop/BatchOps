import unittest
from PIL.Image import Image, new as image_new
import numpy as np
from test_lib import images_jpg_single_dir, test_preset_list

# the module to test
import bg_replacer

# standard preset that will work for testing
standard_replace_bg_preset = bg_replacer.BackgroundSettings(
    name='bg_test',
    background_rgb=(204, 0, 204),  # Pink background
    intensity="natural",
    white_pt=None,
    model_name='u2net'
)

presets = [standard_replace_bg_preset]

## @brief Tests the input validation and helper functions in bg_replacer
#
# These are small unit tests that use tiny generated images, so they
# don't need the image folders or the segmentation model.
class TestBgReplacerValidation(unittest.TestCase):

    ## @brief Checks that a normal RGB tuple is accepted
    # @param self This test object
    def test_validate_rgb_valid(self):
        # Should not raise any errors for standard RGB
        bg_replacer.validate_rgb((0, 128, 255))

    ## @brief Checks that an RGB tuple of the wrong length is rejected
    # @param self This test object
    def test_validate_rgb_invalid_length(self):
        # Should reject tuples that do not have exactly 3 values
        with self.assertRaises(ValueError):
            bg_replacer.validate_rgb((255, 255))

    ## @brief Checks that RGB values outside 0-255 are rejected
    # @param self This test object
    def test_validate_rgb_invalid_value(self):
        # Should reject values outside the 0-255 range
        with self.assertRaises(ValueError):
            bg_replacer.validate_rgb((256, -1, 500))

    ## @brief Checks that a known shadow preset returns its black point and midtones
    # @param self This test object
    def test_get_shadow_preset_valid(self):
        # The 'natural' preset should return (0.00, 1.00)
        black_pt, midtones = bg_replacer.get_shadow_preset("natural")
        self.assertEqual(black_pt, 0.00)
        self.assertEqual(midtones, 1.00)

    ## @brief Checks that an unknown shadow preset name is rejected
    # @param self This test object
    def test_get_shadow_preset_invalid(self):
        with self.assertRaises(ValueError):
            bg_replacer.get_shadow_preset("invalid_preset_name")

    ## @brief Checks that an image with no alpha channel is accepted
    # @param self This test object
    def test_validate_opaque_valid(self):
        # Create a simple RGB image (no alpha channel)
        img = image_new("RGB", (10, 10), (255, 255, 255))
        # Should not raise an error
        bg_replacer.validate_opaque(img)

    ## @brief Checks that an image with transparency is rejected
    # @param self This test object
    def test_validate_opaque_invalid(self):
        img = image_new("RGBA", (10, 10), (255, 255, 255, 0))
        with self.assertRaises(ValueError):
            bg_replacer.validate_opaque(img)

    ## @brief Checks that image_to_array gives a normalised float array
    # @param self This test object
    def test_image_to_array(self):
        img = image_new("RGB", (2, 2), (0, 127, 255))
        arr = bg_replacer.image_to_array(img)

        self.assertEqual(arr.shape, (2, 2, 3))
        self.assertTrue(np.max(arr) <= 1.0)
        self.assertTrue(np.min(arr) >= 0.0)


## @brief Tests background replacing on images
#
# This does several checks on the images:
#   1. output is a Pillow image
#   2. output image dimensions match the inputted images
#   3. output is in standard RGB mode
#   4. (implicitly) background replacing doesn't throw errors
class TestBgReplacer(unittest.TestCase):

    ## @brief Runs background replacement on an image and checks the result
    # @param self This test object
    # @param image The image to replace the background of
    # @param settings The settings to apply when replacing the background
    def replace_background_execution(self,
                                     image: Image,
                                     settings: bg_replacer.BackgroundSettings
                                     ) -> None :

        original_size = image.size
        result_image = bg_replacer.process(image, settings)

        # Ensure the function returned a Pillow Image
        self.assertIsInstance(result_image, Image)

        # Ensure the output image dimensions match the input exactly
        self.assertEqual(result_image.size, original_size)

        # Ensure the final output is in standard RGB mode
        self.assertEqual(result_image.mode, "RGB")

    ## @brief Tests alignment on input JPEG filetype
    # @param self This test object
    def test_replace_works_jpg(self):
        test_preset_list(images_jpg_single_dir, presets, self.replace_background_execution)

if __name__ == '__main__':
    unittest.main()