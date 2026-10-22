import unittest
import PIL.Image
import numpy as np
import os
import sys

# this makes the module to test importable
current_dir = os.path.dirname(os.path.abspath(__file__))
outer_dir = os.path.dirname(current_dir)
sys.path.append(outer_dir)

# the module to test
import bg_replacer

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

if __name__ == '__main__':
    unittest.main()