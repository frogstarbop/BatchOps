import unittest
from PIL.Image import Image

from test_lib import images_jpg_single_dir, test_preset_list

import head_alignment

# standard preset that will work for testing
standard_align_preset = head_alignment.HeadAlignmentSettings(
    name='standard',
    head_x=0.5,
    head_y=0.85
)

# head position that is expected to be to low and will reflect the person
bad_reflect_preset = head_alignment.HeadAlignmentSettings(
    name='bad_reflect',
    head_x=0.5,
    head_y=0.58
)

presets = [standard_align_preset]
fail_presets = [bad_reflect_preset]


## @brief Tests head alignment on JPEG images
#
# This does several checks on the images:
#   1. output is a Pillow image
#   2. output image aspect ratio matches the input
#   3. output is in standard RGB mode
#   4. (implicitly) alignment doesnt throw errors
class TestHeadAlignment(unittest.TestCase):
    ## @brief Runs alignment on an image and checks the result
    # @param self This test object
    # @param image The image to align
    # @param settings The settings to apply when aligning
    def align_image(self,
                    image: Image,
                    settings: head_alignment.HeadAlignmentSettings
                    ) -> None:
        original_ratio = image.width / image.height
        result_image = head_alignment.process(image, settings)

        # Ensure the function returned a Pillow Image
        self.assertIsInstance(result_image, Image)

        # Ensure the output image keeps the same aspect ratio
        self.assertAlmostEqual(original_ratio, result_image.width / result_image.height, 2)

        # Ensure the final output is in standard RGB mode
        self.assertEqual(result_image.mode, "RGB")

    ## @brief Check that alignment with an impossible head position fails
    # @param self This test object
    # @param image The image to align
    # @param settings The alignment settings to apply
    def align_image_fail(self,
                         image: Image,
                         settings: head_alignment.HeadAlignmentSettings
                         ) -> None:

        # expect alignment to raise an error, fail the test if not
        with self.assertRaises(Exception):
            head_alignment.process(image, settings)

        print('threw as expected')
        image.close()

    ## @brief Tests alignment on input JPEG filetype
    # @param self This test object
    def test_align_jpg(self):
        test_preset_list(images_jpg_single_dir, presets, self.align_image)

    ## @brief Tests that alignment with impossible settings does fail
    # @param self This test object
    def test_failure(self):
        test_preset_list(images_jpg_single_dir, fail_presets, self.align_image_fail)


# allow to run tests individually
if __name__ == '__main__':
    unittest.main()