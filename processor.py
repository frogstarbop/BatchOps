from settings import Settings
from folder_manager import FolderManager, FolderError
import PIL.Image
import compression
import cropping
import io
import threading
import queue

# splitting image processing from the queue for obv reasons
# settings -> error handling
def process_image(settings: Settings):

    # TODO: make every applied process occur (get it out of an elif)
    # TODO: make processes actually apply instead of magical theories
    # TODO: more comments when im not sleep deprived
    if settings.cropping_enabled:
        try:
            image = cropping.process(image, settings.cropping_enabled)
        except:
            # TODO: better handling errors, put in own dir
            # error_dir.write_file(file_name, data) - invent an error dir but sleep first
            print('failed to crop ' + file_name)
    elif settings.headalg_enabled:
        try:
            print('placeholder')
        except:
            print('head alignment failed on ' + file_name)
    elif settings.compression_enabled:
        try:
            image = compression.process(image, settings.compression_enabled)
        except:
            print('head alignment failed on ' + file_name)
    else:
        try:
            print('placeholder')
        except:
            print('head alignment failed on ' + file_name)

    data: bytes
    if settings.compression_enabled:
        try:
            data = compression.process(image, settings.compression)
        except:
            print('failed to compress ' + file_name)
    else:
        # TODO: better handling errors, put in own dir
        data = backup_get_image_data(image)


def processing(settings: Settings, in_dir: FolderManager, out_dir: FolderManager):
    in_dir.validate()
    out_dir.validate()

    # no more items will be coming, so the queue is 'finished'. Avoids inf. looping in the true and (hopefully) makes threads easier to manage? we find out!
    fin_flag = ''

    in_queue: queue.Queue = queue.Queue(maxsize=8)
    out_queue: queue.Queue = queue.Queue(maxsize=8)

    # metaphorical threads/proceeses start HERE (probs)

    def readin():
        try: 
            image: PIL.Image.Image
            for image in in_dir:
                file_name = getattr(image, 'filename', None)
                assert file_name is not None
                in_queue.put((file_name, image))
        except: 
            print("error occurred at " + file_name)
        finally:
            # tells processor_operations when to stop neatly
            in_queue.put(fin_flag)

    def processor_operations():
        try:
            while True:
                item = in_queue.get()
                # Essentially if there is nothing in the queue, kill this loop dead.
                if item is fin_flag:
                    break
                file_name, data = item
                data = process_image(settings, file_name, image)
                if data is not None:
                    out_queue.put(file_name, data)
        except Exception as e:
            print("Exception " + e + "Occurred")
        finally:
            out_queue.put(fin_flag)

    # Metaphorical threads/processes close here

    # Print out everything from the out queue
    while True:
        item = out_queue.get()
        if item is fin_flag:
            break
        file_name, data = item
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