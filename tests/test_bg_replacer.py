import unittest
import PIL.Image
import numpy as np

from test_lib import images_jpg_single_dir, test_folder

# the module to test
import bg_replacer


preset = bg_replacer.BackgroundSettings(
    name='stest',
    background_rgb=(204, 0, 204),  # Pink background
    intensity="natural",
    white_pt=None,
    model_name='u2net'
)

class TestBgReplacerValidation(unittest.TestCase):

    def test_validate_rgb_valid(self):
        # Should not raise any errors for standard RGB
        bg_replacer.validate_rgb((0, 128, 255))

    def test_validate_rgb_invalid_length(self):
        # Should reject tuples that do not have exactly 3 values
        with self.assertRaises(ValueError):
            bg_replacer.validate_rgb((255, 255))

    def test_validate_rgb_invalid_value(self):
        # Should reject values outside the 0-255 range
        with self.assertRaises(ValueError):
            bg_replacer.validate_rgb((256, -1, 500))

    def test_get_shadow_preset_valid(self):
        # The 'natural' preset should return (0.00, 1.00)
        black_pt, midtones = bg_replacer.get_shadow_preset("natural")
        self.assertEqual(black_pt, 0.00)
        self.assertEqual(midtones, 1.00)

    def test_get_shadow_preset_invalid(self):
        with self.assertRaises(ValueError):
            bg_replacer.get_shadow_preset("invalid_preset_name")

    def test_validate_opaque_valid(self):
        # Create a simple RGB image (no alpha channel)
        img = PIL.Image.new("RGB", (10, 10), (255, 255, 255))
        # Should not raise an error
        bg_replacer.validate_opaque(img)

    def test_validate_opaque_invalid(self):
        # Create an RGBA image with a transparent pixel
        img = PIL.Image.new("RGBA", (10, 10), (255, 255, 255, 0))
        with self.assertRaises(ValueError):
            bg_replacer.validate_opaque(img)

    def test_image_to_array(self):
        # Tests that images convert into normalized 0.0-1.0 float arrays
        img = PIL.Image.new("RGB", (2, 2), (0, 127, 255))
        arr = bg_replacer.image_to_array(img)

        self.assertEqual(arr.shape, (2, 2, 3))
        self.assertTrue(np.max(arr) <= 1.0)
        self.assertTrue(np.min(arr) >= 0.0)


class TestBgReplacer(unittest.TestCase):

    def replace_background_execution(self, image: PIL.Image.Image, settings: bg_replacer.BackgroundSettings):
        """Tests that the main function processes an image and returns a valid output."""

        # If the image is missing, PIL will raise a FileNotFoundError and fail the test,
        original_size = image.size
        result_image = bg_replacer.process(image, settings)

        # Ensure the function returned a Pillow Image
        self.assertIsInstance(result_image, PIL.Image.Image)

        # Ensure the output image dimensions match the input exactly
        self.assertEqual(result_image.size, original_size)

        # Ensure the final output is in standard RGB mode
        self.assertEqual(result_image.mode, "RGB")

    def test_replace_works_jpg(self):
        test_folder(images_jpg_single_dir, preset, self.replace_background_execution)

if __name__ == '__main__':
    unittest.main()