import PIL.Image
import PIL.ImageOps
import io
import os

def cropping(image: PIL.Image.Image, width_ratio: int, height_ratio: int) -> PIL.Image.Image:

    original_width, original_height = image.size;

    # checks if the ratio of orignaal image has ratio resulting in more width thus width will have to be cut
    if (original_width / original_height) > (width_ratio / height_ratio):
        size = (int(original_height * (width_ratio / height_ratio)), original_height)
    # if ratio has more height cut the height
    else :
        size = (original_width, int(original_width * (height_ratio / width_ratio)))

    cropped_image = PIL.ImageOps.fit(image, size);

    return cropped_image