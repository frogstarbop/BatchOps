import PIL.Image
import io
import os

# TODO: rescale image on first attempt not small enough

## @brief Compresses a given image into a JPEG
#
# This compresses a given image from whatever format into an optimized JPEG
# image
#
# @returns A byte array containing the data of the compressed JPEG
def process(image: PIL.Image.Image) -> bytes:
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
    image.save(virtual_file, format='JPEG', optimize=True)
    data: bytes = virtual_file.getvalue()

    # display output image filesize
    file_size = len(data)
    print(f'compressed image virtual filesize is\t{file_size: 10d}')

    # display size of output image as percent of input image
    compression_ratio = (original_file_size - file_size) * 100 / original_file_size
    print(f'compression ratio of {compression_ratio: 5.1f}%')

    return data