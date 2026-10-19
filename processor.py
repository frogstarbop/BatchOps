import io
import time
import queue
import PIL.Image
import threading
from pathlib import Path

from settings import Settings
from folder_manager import FolderManager, FolderError
import image_compression as compression
import bg_replacer as bg_removal
import cropping

QUEUE_WAITING_SLEEP_SECONDS: float = 0.05
QUEUE_SHORT_SLEEP_SECONDS: float = 0.01

# splitting image processing from the queue for obv reasons
# will throw any errors faced during processing step running
# settings -> error handling
def process_image(image: PIL.Image.Image, settings: Settings) -> bytes:
    # process-steps are done in order of least destructive to most
    # so compression is most destructive so MUST be last
    # cropping AFTER head_alignment (head alignment can change aspect ratio)
    # bg_removal is least destructive so goes first

    if settings.bg_removal_enabled:
        assert settings.bg_removal is not None
        image = bg_removal.process(image, settings.bg_removal)

    if settings.head_alignment_enabled:
        assert settings.head_alignment is not None
        # TODO: uncomment when head_alignment implemented
        # image = head_alignment.process(image, settings.head_alignment)

    if settings.cropping_enabled:
        assert settings.cropping is not None
        image = cropping.process(image, settings.cropping)

    data: bytes
    if settings.compression_enabled:
        assert settings.compression is not None
        data = compression.process(image, settings.compression)
    else:
        data = backup_get_image_data(image)
    return data

def process(settings: Settings, in_dir: FolderManager, out_dir: FolderManager):
    in_dir.validate()
    out_dir.validate()

    # no more items will be coming, so the queue is 'finished'. Avoids inf. looping in the true and (hopefully) makes threads easier to manage? we find out!
    fin_flag = None

    # for the queues, 'None' is an finish-flag
    in_queue: queue.Queue[PIL.Image.Image|None] = queue.Queue(maxsize=8)
    # no max size for err_queue, should not fill up
    err_queue: queue.Queue[tuple[PIL.Image.Image,Exception]] = queue.Queue()
    out_queue: queue.Queue[tuple[str,bytes]|None] = queue.Queue(maxsize=8)

    # setup a shared error output directory
    assert out_dir.path is not None
    err_dir: FolderManager = FolderManager('error', False)
    err_path: Path = out_dir.path.with_name(out_dir.path.name + '_errors')
    err_dir.set_path(str(err_path))

    # setup the iterator over the input directory
    in_iter = iter(in_dir)

    # a thread which constantly tries to load/save files for the queues
    # instead of reading the whole input folder into the input queue immediately
    def file_IO_looper():
        nonlocal in_queue
        nonlocal out_queue
        nonlocal err_queue
        nonlocal fin_flag
        nonlocal in_iter
        nonlocal err_dir

        while True:
            # prioritize outputting
            if not out_queue.empty():
                item: tuple[str,bytes]|None = out_queue.get()

                if item == None:
                    # stop once all processes put a fin flag in queue
                    # TODO: count that there have been N fin flags
                    print('file io looper received fin flag, stopping')
                    return

                file_name: str = item[0]
                data: bytes = item[1]
                out_dir.write_file(file_name, data)
                print(f'file io: wrote image {file_name}')

            elif not err_queue.empty():
                item2: tuple[PIL.Image.Image,Exception] = err_queue.get()
                image: PIL.Image.Image = item2[0]
                error: Exception = item2[1]

                file_name: str = getattr(image, 'filename')
                assert file_name is not None
                data: bytes = backup_get_image_data(image)

                # TODO: save each type of processing-step error to a different dir
                err_dir.write_file(file_name, data)

            elif not in_queue.full():
                try:
                    image: PIL.Image.Image = next(in_iter)

                    file_name = getattr(image, 'filename')
                    assert file_name is not None
                    print(f'file io: read image {file_name}')
                except StopIteration:
                    in_queue.put(fin_flag)
            else:
                # nothing to do, sleep for a short while
                time.sleep(QUEUE_SHORT_SLEEP_SECONDS)

    file_IO_thread: threading.Thread = threading.Thread(target=file_IO_looper)
    file_IO_thread.start()
    print('file io thread started')

    def processing_looper():
        nonlocal in_queue
        nonlocal err_queue
        nonlocal out_queue
        nonlocal fin_flag
        nonlocal settings

        while True:
            # wait until there is something to process
            if in_queue.empty():
                time.sleep(QUEUE_WAITING_SLEEP_SECONDS)

            image: PIL.Image.Image|None = in_queue.get()

            # if receive fin flag, processing complete
            if image is None:
                # put fin flag into output queue to let other threads know
                out_queue.put(fin_flag)
                return

            file_name:str = getattr(image, 'filename')
            assert file_name is not None
            try:
                data = process_image(image, settings)

                # wait for a space in the output queue to put the image
                while out_queue.full():
                    time.sleep(QUEUE_WAITING_SLEEP_SECONDS)

                out_queue.put((file_name, data))
            # handle each processing-step's errors
            except compression.CompressionError as e:
                print(f'COMPRESSION error on file {file_name}: {e}')
                err_queue.put((image, e))
            # TODO: HANDLE ERRORS FROM ALL TYPES OF process-steps
            # generic error handling
            except Exception as e:
                print(f'UNEXPECTED Exception {e} Occurred')
                err_queue.put((image, e))

    # TODO: make processing run on another process if threading not splitting across CPU cores
    # TODO: make multiple of these run at once
    processing_thread: threading.Thread = threading.Thread(target=processing_looper)
    processing_thread.start()
    print('processing thread started')

    processing_thread.join()
    print('processing thread completed')

    file_IO_thread.join()
    print('file IO thread completed')

    print('processing completed')
            
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
        name='standard',
        max_file_size=600 * 1000,
        preferred_widths=[1280, 1920, 2560],
        min_height=720,
        quality=75
    ),
    bg_removal_enabled=False,
    bg_removal=None,
    head_alignment_enabled=False,
    head_alignment=None,
    cropping_enabled=False,
    cropping=None
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