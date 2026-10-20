from dataclasses import dataclass
import PIL.Image
import PIL.ImageOps
import io
import os

## @brief a container for all the settings for cropping an image
@dataclass
class CroppingSettings:
    name: str
    width_ratio: int
    height_ratio: int

def process(image: PIL.Image.Image, settings: CroppingSettings) -> PIL.Image.Image:

    original_width, original_height = image.size;
    width_ratio: int = settings.width_ratio
    height_ratio: int = settings.height_ratio

    # checks if the ratio of orignaal image has ratio resulting in more width thus width will have to be cut
    if (original_width / original_height) > (width_ratio / height_ratio):
        size = (int(original_height * (width_ratio / height_ratio)), original_height)
    # if ratio has more height cut the height
    else :
        size = (original_width, int(original_width * (height_ratio / width_ratio)))

    cropped_image = PIL.ImageOps.fit(image, size);

    return cropped_image