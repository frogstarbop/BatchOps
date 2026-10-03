import PIL.Image
import io
import os

from dataclasses import dataclass

## @brief A container for all the settings for compressing an image
@dataclass
class CompressionSettings:
    ## The maximum allowed output byte array size in bytes
    max_file_size: int

    ## Convenient or common widths in pixels that images should try use
    preferred_widths: list[int]

    ## The minimum allowable height in pixels of the output image
    min_height: int

    ## The JPEG compression level (0-100)
    #  normal range is 75-90
    #  where 0 is worst quality but smallest file,
    #  100 is beeest quality but huge file
    quality: int

# TODO: rescale image on first attempt not small enough

## @brief Compresses a given image into a JPEG
#
# This compresses a given image from whatever format into an optimized JPEG
# image
#
# @param image The image to be compressed
# @param settings The details of how much compression and decision boundaries
# @returns A byte array containing the data of the compressed JPEG
def process(image: PIL.Image.Image, settings: CompressionSettings) -> bytes:
    # TODO: use all fields of settings

    # create an in-memory byte buffer than can be written to and read from
    virtual_file: io.BytesIO = io.BytesIO()

    # get the filename of the image
    filename: str | None = getattr(image,'filename', None)
    assert filename is not None

    # output the input filesize
    file_size: int = os.path.getsize(filename)
    print(f'original input image filesize is\t{file_size: 10d}')
    original_file_size: int = file_size

    # compress the image
    image.save(virtual_file,
               format='JPEG',
               optimize=True,
               quality=settings.quality,
    )
    data: bytes = virtual_file.getvalue()

    # display output image filesize
    file_size = len(data)
    print(f'compressed image virtual filesize is\t{file_size: 10d}')

    # display size of output image as percent of input image
    compression_ratio = (original_file_size - file_size) * 100 / original_file_size
    print(f'compression ratio of {compression_ratio: 5.1f}%')

    return data