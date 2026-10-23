from collections.abc import Callable
from os.path import join
from os.path import isfile
from os.path import dirname
from os.path import abspath
from os import listdir
from PIL.Image import open
from PIL.Image import Image
from typing import TypeVar

# this makes the modules to test importable
import sys
current_dir = dirname(abspath(__file__))
outer_dir = dirname(current_dir)
sys.path.append(outer_dir)

from image_compression import CompressionSettings
from bg_replacer import BackgroundSettings
from head_alignment import HeadAlignmentSettings
from cropping import CroppingSettings

# constants
images_src_dir: str = 'images'
images_jpg_dir: str = join(images_src_dir, 'jpeg')
images_png_dir: str = join(images_src_dir, 'png')
images_compression_failure: str = join(images_src_dir, 'compression_specific')
images_jpg_single_dir: str = join(images_jpg_dir, 'studio_single')

SettingsType = TypeVar('SettingsType', CroppingSettings, CompressionSettings, BackgroundSettings, HeadAlignmentSettings)

## @brief Runs a test on every image in a folder recursively
# @param self This test object
# @param sub_directory The path containing the image files
# @param settings The settings to apply when running the test
def test_folder[SettingsType](
            sub_directory: str,
            settings: SettingsType,
            process_step: Callable[[Image, SettingsType], None]
            ) -> None:
    print(f'----TESTING FOLDER {sub_directory}----')
    for file_name in listdir(sub_directory):
        file_path = join(sub_directory, file_name)
        if not isfile(file_path):
            # go in recursively
            test_folder(file_path, settings, process_step)
            continue
        test_process_step(file_path, settings, process_step)

## @brief Tests presets on jpeg inputs
# @param self This test object
def test_preset_list[SettingsType](
                        image_path: str,
                        presets: list[SettingsType],
                        process_step: Callable[[Image, SettingsType], None]
                        ) -> None:
    for preset in presets:
        print(f'----TESTING PRESET {preset.name}----')
        test_folder(image_path, preset, process_step)

def test_process_step[SettingsType](file_path: str, settings: SettingsType, process_step: Callable[[Image, SettingsType], None]):
    print('loading file ' + file_path)
    image: Image = open(file_path)
    image.load()
    process_step(image, settings)
    image.close()