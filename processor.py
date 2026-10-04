from settings import Settings
from folder_manager import FolderManager, FolderError
import PIL.Image
import compression
import io

def process(settings: Settings, in_dir: FolderManager, out_dir: FolderManager):
    in_dir.validate()
    out_dir.validate()

    # TODO: do processing on another thread
    # TODO: read into queue
    image: PIL.Image.Image
    for image in in_dir:
        file_name = getattr(image, 'filename', None)
        assert file_name is not None

        # TODO: cropping
        # if settings.cropping_enabled:
        #     try:
        #         image = cropping.process(image, settings.cropping_enabled)
        #     except:
        #         # TODO: better handling errors, put in own dir
        #         print('failed to crop ' + file_name)
        # TODO: head_alignment
        # TODO: bg_removal

        data: bytes
        if settings.compression_enabled:
            try:
                data = compression.process(image, settings.compression)
            except:
                print('failed to compress ' + file_name)
                continue
        else:
            # TODO: better handling errors, put in own dir
            data = backup_get_image_data(image)

        # ensure output image has correct filetype
        file_type = file_name.split('.')[-1]
        out_file_name = file_type.split

        # TODO: write into queue
        out_dir.write_file(file_name, data)

def backup_get_image_data(image: PIL.Image.Image) -> bytes:
    # create an in-memory byte buffer than can be written to and read from
    virtual_file: io.BytesIO = io.BytesIO()

    # encode image
    image.save(virtual_file, format='JPEG')

    data = virtual_file.getvalue()
    virtual_file.close()
    return data

# TODO: this is a temporary test for before a whole test script is made
# MUST BE RUNNING FROM PROJECT ROOT DIR (NOT TESTS DIR)
settings = Settings(
    compression_enabled=True,
    compression=compression.CompressionSettings(
        # yoinked from compression_tests.py
        max_file_size=600 * 1000,
        preferred_widths=[1280, 1920, 2560],
        min_height=720,
        quality=75
    )
)

in_dir = FolderManager('from', True)
out_dir = FolderManager('to', False)
print('out dir is input ' + str(out_dir.is_input))
in_dir.set_path('./tests/images/jpeg/outdoors')
out_dir.set_path('./tests/images/output')

try:
    process(settings, in_dir, out_dir)
except FolderError as e:
    print('failed to process: folder error: ' + e.path + ' ' + str(e))