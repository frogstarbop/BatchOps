import PIL.Image
import io
import os

def compress(image: PIL.Image.Image) -> bytes:
    virtual_file: io.BytesIO = io.BytesIO()
    filename: str | None = getattr(image,'filename', None)
    assert filename is not None

    file_size: int = os.path.getsize(filename)
    print(f'original input image filesize is\t{file_size: 10d}')
    original_file_size: int = file_size

    image.save(virtual_file, format='JPEG', optimize=True)
    data: bytes = virtual_file.getvalue()

    file_size = len(data)
    print(f'compressed image virtual filesize is\t{file_size: 10d}')

    compression_ratio = (original_file_size - file_size) * 100 / original_file_size
    print(f'compression ratio of {compression_ratio: 5.1f}%')

    return data