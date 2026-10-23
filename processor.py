import io
import os
import time
import PIL.Image
import PIL.ImageOps
import traceback
import threading
import queue
from multiprocessing import Process, Queue
import multiprocessing
from pathlib import Path

from settings import Settings
from folder_manager import FolderManager, FolderError
import image_compression as compression
import bg_replacer as bg_removal
import head_alignment
import cropping

QUEUE_WAITING_SLEEP_SECONDS: float = 0.05
QUEUE_SHORT_SLEEP_SECONDS: float = 0.01

### stats section ###
# statistics to show for ui
stats_image_count_total = 0
stats_image_count_success = 0
stats_image_count_failed = 0
stats_time_started = 0

## @brief Gets the current time IN SECONDS since epoch
def get_now() -> int:
    return int(time.time()) 
def mark_start_time() -> None:
    global stats_time_started
    stats_time_started = get_now()

# getters
def get_images_total() -> int:
    global stats_image_count_total
    return stats_image_count_total
def get_images_success() -> int:
    global stats_image_count_success
    return stats_image_count_success
def get_images_failed() -> int:
    global stats_image_count_failed
    return stats_image_count_failed

## @brief get the progress as a float value (QoL getter)
def get_progress() -> float:
    global stats_image_count_total
    global stats_image_count_success
    global stats_image_count_failed
    if stats_image_count_total == 0:
        return 0
    images_done = stats_image_count_success + stats_image_count_failed
    return images_done / stats_image_count_total

## @brief Get seconds remaining estimate
def get_estimated_time_left() -> int:
    global stats_time_started
    delta_time = get_now() - stats_time_started

    progress = get_progress()
    if progress < 0.00001:
        return -1
    total_time = delta_time / progress
    time_left = total_time - delta_time
    return int(time_left)

### main section ###
# splitting image processing from the queue for obv reasons
# will throw any errors faced during processing step running
# settings -> error handling
def process_image(image: PIL.Image.Image, settings: Settings) -> tuple[bool, bytes, str]:
    file_name: str | None = getattr(image, 'filename', None)
    assert file_name is not None

    # apply the EXIF rotation so the image is upright (bg_removal expects it, and saving drops the tag)
    image = PIL.ImageOps.exif_transpose(image)
    
    # process-steps are done in order of least destructive to most
    # so compression is most destructive so MUST be last
    # cropping AFTER head_alignment (head alignment can change aspect ratio)
    # bg_removal is least destructive so goes first

    if settings.bg_removal_enabled:
        assert settings.bg_removal is not None
        try:
            image = bg_removal.process(image, settings.bg_removal)
        except Exception as e:
            print(e)
            return False, bytes(0), 'background_removal'

    if settings.head_alignment_enabled:
        assert settings.head_alignment is not None
        try:
            image = head_alignment.process(image, settings.head_alignment)
        except Exception as e:
            print(e)
            return False, bytes(0), 'head_alignment'

    if settings.cropping_enabled:
        assert settings.cropping is not None
        try:
            image = cropping.process(image, settings.cropping)
        except Exception as e:
            print(e)
            return False, bytes(0), 'head_alignment'

    # JPEG can't store transparency or palettes
    if image.mode != 'RGB':
        image = image.convert('RGB')

    data: bytes
    if settings.compression_enabled:
        assert settings.compression is not None
        print('running compression')
        try:
            data = compression.process(image, settings.compression, file_name)
            print('compression succeeded')
        except Exception as e:
            print(e)
            return False, bytes(0), 'compression'
    else:
        data = backup_get_image_data(image)
    return True, data, ''

def process(settings: Settings, in_dir: FolderManager, out_dir: FolderManager):
    global stats_image_count_total
    global stats_image_count_success
    global stats_image_count_failed

    try:
        in_dir.validate()
        out_dir.validate()
    except FolderError as e:
        print(f'FOLDER ERROR: {e.path} {e}')
        return

    # no more items will be coming, so the queue is 'finished'. Avoids inf. looping in the true and (hopefully) makes threads easier to manage? we find out!
    fin_flag = None

    # for the queues, 'None' is an finish-flag
    in_queue: Queue[PIL.Image.Image|None] = Queue(maxsize=8)
    # no max size for err_queue, should not fill up
    err_queue: Queue[tuple[PIL.Image.Image,str]] = Queue()
    out_queue: Queue[tuple[str,bytes]|None] = Queue(maxsize=8)

    # setup a shared error output directory
    assert out_dir.path is not None
    err_dir: FolderManager = FolderManager('error', False)
    err_path: Path = out_dir.path.with_name(out_dir.path.name + '_errors')
    err_dir.set_path(str(err_path))

    # stats init
    mark_start_time()
    stats_image_count_total = in_dir.count_images()
    stats_image_count_failed = 0
    stats_image_count_success = 0

    # setup the iterator over the input directory
    in_iter = iter(in_dir)

    # pre-calculate how many subprocesses will be made
    subprocess_count = os.cpu_count() or 1
    subprocess_count = max(subprocess_count - 2, 1)

    # these use too much RAM to have multiple processing at once
    if settings.bg_removal_enabled or settings.head_alignment_enabled:
        subprocess_count = 1

    # a thread which constantly tries to load/save files for the queues
    # instead of reading the whole input folder into the input queue immediately
    # also handles updating stat image counts
    def file_IO_looper():
        global stats_image_count_failed
        global stats_image_count_success

        print('file io: starting')

        # drains every waiting error, not just one
        def flush_errs(timeout: float):
            while True:
                try:
                    file_name, errsub_dir = err_queue.get(timeout=timeout)
                    save_errored_image(file_name, errsub_dir, err_dir)
                except queue.Empty:
                    return

        to_send: list[str | None] = []   # paths (then stop flags) waiting for room in in_queue
        exhausted = False                # True once the input folder is fully read
        recv_stops = 0

        while True:
            flush_errs(0.001)

            # output side
            try:
                item = out_queue.get(timeout=0.01)
                if item is None:
                    recv_stops += 1
                    if recv_stops >= subprocess_count:
                        flush_errs(0.5)   # errors travel on a separate pipe, give stragglers a moment
                        print('file io looper received fin, stopping')
                        in_queue.close()
                        err_queue.close()
                        out_queue.close()
                        return
                else:
                    file_name, data = item
                    try:
                        out_dir.write_file(file_name, data)
                        stats_image_count_success += 1
                        print(f'file io: wrote image {file_name}')
                    except Exception as e:
                        print(f"file io: failed to write {file_name}:{e}")
                        stats_image_count_failed += 1
            except queue.Empty:
                pass

            # input side: never block on a full in_queue
            if not exhausted and not to_send:
                try:
                    image = next(in_iter)
                    to_send.append(image.filename)
                    image.close()
                except StopIteration:
                    to_send.extend([fin_flag] * subprocess_count)
                    exhausted = True

            if to_send:
                try:
                    in_queue.put_nowait(to_send[0])
                    to_send.pop(0)
                except queue.Full:
                    pass

    file_IO_thread: threading.Thread = threading.Thread(target=file_IO_looper)
    file_IO_thread.start()
    print('file io thread started')

    # TODO: fix deadlock bug on final images from input queue
    subprocess_count = 1
    # multiprocessing.set_start_method("spawn", force=True) is necessary for Windows to avoid issues with forking processes. It ensures that each subprocess starts fresh and can properly import the necessary modules.
    # It is also necessary to avoid conflicts with older versions of Python, when using fork on 3.14>, nested functions can't be pickled.
    multiprocessing.set_start_method("spawn", force=True)

    # start the processing subprocesses
    for i in range(subprocess_count):
        processing_thread: Process = Process(target=processing_looper, args=(in_queue, err_queue, out_queue, settings))
        processing_thread.start()
    print('processing process started')
            



## @brief Worker process entry point. Must be top-level so spawn can pickle it by name
def processing_looper(in_queue, err_queue, out_queue, settings: Settings):
    print('processing looper: started')

    while True:
        file_name = in_queue.get()

        if file_name is None:
            out_queue.put(None)
            print('processing looper: received fin flag')
            return

        print(f'processing received {file_name}')
        try:
            with PIL.Image.open(file_name) as image:
                success, data, error_subdir = process_image(image, settings)
                print(f'{success} {error_subdir}')
                if not success:
                    err_queue.put((file_name, error_subdir))
                else:
                    out_queue.put((Path(file_name).stem + '.jpg', data))
        except Exception as e:
            # Provide a descriptive error message and traceback for debugging purposes. The error is also sent to the error queue for further handling.
            print(f'Exception on {file_name}:\n{traceback.format_exc()}')
            err_queue.put((file_name, str(e)))   # strings pickle safely, exceptions don't always


## @brief saves an image that failed processing into the error folder and counts it as failed
def save_errored_image(file_name: str, err_sub_dir: str, err_dir: FolderManager) -> None:
    global stats_image_count_failed
    print(f'error subdir is {err_sub_dir}')
    try:
        with PIL.Image.open(file_name) as image:
            new_name = Path(file_name).stem + '.jpg'
            err_dir.write_file_subfolder(err_sub_dir, new_name, backup_get_image_data(image))
    except Exception as e:
        print(f"could not save the errored image: {e}")
    stats_image_count_failed += 1


def backup_get_image_data(image: PIL.Image.Image) -> bytes:
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # create an in-memory byte buffer than can be written to and read from
    virtual_file: io.BytesIO = io.BytesIO()

    # encode image
    image.save(virtual_file, format='JPEG')

    data = virtual_file.getvalue()
    virtual_file.close()
    return data