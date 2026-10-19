import PIL.Image
import io
import os

from dataclasses import dataclass

class CompressionError(Exception):
    pass

## @brief A container for all the settings for compressing an image
@dataclass
class CompressionSettings:
    ## The name of this setting
    name: str

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

## @brief Finds the value from widths smaller than width
# @returns smallest width or -1 if width is smaller than smallest in widths
def next_width(width: int, widths: list[int]) -> int:
    for preffered_width in widths:
        if width > preffered_width:
            return preffered_width
    return -1


def get_image_data(image: PIL.Image.Image, settings: CompressionSettings) -> tuple[bytes, int]:
    # create an in-memory byte buffer than can be written to and read from
    virtual_file: io.BytesIO = io.BytesIO()

    image.save(virtual_file,
            format='JPEG',
            optimize=True,
            quality=settings.quality,
    )

    data: bytes = virtual_file.getvalue()
    virtual_file.close()

    return data, len(data)

## @brief Compresses a given image into a JPEG
#
# This compresses a given image from whatever format into an optimized JPEG
# image
#
# @param image The image to be compressed
# @param settings The details of how much compression and decision boundaries
# @returns A byte array containing the data of the compressed JPEG
def process(image: PIL.Image.Image, settings: CompressionSettings) -> bytes:
    # ensure widths are in descending order
    widths = sorted(settings.preferred_widths,reverse=True)

    # get the filename of the image
    filename: str | None = getattr(image,'filename', None)
    assert filename is not None

    # log the input filesize
    file_size: int = os.path.getsize(filename)
    print(f'original input image filesize is\t{file_size: 10d}')
    original_file_size: int = file_size

    # check if image too short
    if image.height < settings.min_height:
        raise CompressionError(f'{filename}: input is {image.height}px tall, min is {settings.min_height}px')

    # check if input filesize already under max filesize
    data, file_size = get_image_data(image, settings)
    if file_size <= settings.max_file_size:
        print('skipping image, already undersized')

    while file_size > settings.max_file_size:
        # compress the image
        data, file_size = get_image_data(image, settings)

        # display output image filesize
        print(f'compressed image virtual filesize is\t{file_size: 10d}')

        #if too large, reduce width
        if file_size > settings.max_file_size:
            new_width: int = next_width(image.width, widths)
            print(f'old width is {image.width}, new width is {new_width}')
            aspect_ratio: float = image.width / image.height
            expected_height: int = round(new_width / aspect_ratio)

            # if reducing breaks a rule, fail this image
            if new_width == -1:
                max_KB: int = settings.max_file_size//1000
                raise CompressionError(f'{filename}: could not be compressed to fit under {max_KB}KB, hit preffered width limit')
            if expected_height < settings.min_height:
                max_KB: int = settings.max_file_size//1000
                raise CompressionError(f'{filename}: could not be compressed to fit under {max_KB}KB, hit min height limit')
            # resize image
            new_size = (new_width, expected_height)
            sampling = PIL.Image.Resampling.BICUBIC
            image = image.resize(new_size, sampling)

    # display size of output image as percent of input image
    compression_ratio: float = (original_file_size - file_size) * 100 / original_file_size
    print(f'compression ratio of {compression_ratio: 5.1f}%')

    return data