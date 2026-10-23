import PIL.Image
import unittest

from test_lib import test_preset_list, images_jpg_dir
import cropping

presets = [
    cropping.CroppingSettings(
        name='desktop',
        width_ratio=16,
        height_ratio=9
    ),
    cropping.CroppingSettings(
        name='square',
        width_ratio=1,
        height_ratio=1
    ),
    cropping.CroppingSettings(
        name='tall',
        width_ratio=9,
        height_ratio=16
    ),
]

class TestCropping(unittest.TestCase):
    def crop_image(self, image: PIL.Image.Image, settings: cropping.CroppingSettings):
        cropped_image = cropping.process(image, settings)

        AR = cropped_image.width / cropped_image.height
        TAR = settings.width_ratio / settings.height_ratio

        # allow off by one errors, but output should be the right aspect ratio
        self.assertAlmostEqual(AR, TAR, 2)

    def test_cropping_doesnt_crash(self):
        test_preset_list(images_jpg_dir, presets, self.crop_image)

if __name__ == "__main__":
    unittest.main()