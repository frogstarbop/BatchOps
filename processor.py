import io
import os
import time
import PIL.Image
import PIL.ImageOps
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
def process_image(image: PIL.Image.Image, settings: Settings) -> bytes:
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
        image = bg_removal.process(image, settings.bg_removal)

    if settings.head_alignment_enabled:
        assert settings.head_alignment is not None
        image = head_alignment.process(image, settings.head_alignment)

    if settings.cropping_enabled:
        assert settings.cropping is not None
        image = cropping.process(image, settings.cropping)

    # JPEG can't store transparency or palettes
    if image.mode != 'RGB':
        image = image.convert('RGB')

    data: bytes
    if settings.compression_enabled:
        assert settings.compression is not None
        data = compression.process(image, settings.compression, file_name)
    else:
        data = backup_get_image_data(image)
    return data

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
    err_queue: Queue[tuple[PIL.Image.Image,Exception]] = Queue()
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
        nonlocal in_queue
        nonlocal out_queue
        nonlocal err_queue
        nonlocal fin_flag
        nonlocal in_iter
        nonlocal err_dir
        nonlocal subprocess_count
        global stats_image_count_failed
        global stats_image_count_success

        print('file io: starting')

        def flush_errs():
            nonlocal err_queue
            nonlocal err_dir
            try:
                image: PIL.Image.Image
                err: Exception
                image, err = err_queue.get(timeout=0.01)
                print('file io: handling error')
                save_errored_image(image, err, err_dir)
            except ValueError:
                return
            except queue.Empty:
                return

        sent_stop: bool = False
        recv_stops: int = 0

        while True:
            flush_errs()
            # prioritize outputting
            try:
                item: tuple[str,bytes]|None = out_queue.get(timeout=0.01)

                # stop once all processes put a fin flag in queue
                if item == None:
                    recv_stops += 1
                    if recv_stops >= subprocess_count:
                        print('file io looper received fin, stopping')
                        if not sent_stop:
                            raise RuntimeError('Receiving stop before send stop')
                        flush_errs()
                        in_queue.close()
                        err_queue.close()
                        out_queue.close()
                        return
                    continue

                file_name: str = item[0]
                data: bytes = item[1]
                try:

                    out_dir.write_file(file_name, data)
                    stats_image_count_success += 1
                    print(f'file io: wrote image {file_name}')
                except Exception as e:
                    print(f"file io: failed to write {file_name}:{e}")
                    stats_image_count_failed += 1
            except ValueError:
                pass
            except queue.Empty:
                pass
            if not sent_stop:
                try:
                    image: PIL.Image.Image = next(in_iter)
                    file_name = getattr(image, 'filename')
                    assert file_name is not None
                    print(f'file io: read image {file_name}')
                    in_queue.put(image)
                except StopIteration:
                    for i in range(subprocess_count):
                        in_queue.put(fin_flag)
                    sent_stop = True
            else:
                # nothing to do, sleep for a short while
                time.sleep(QUEUE_SHORT_SLEEP_SECONDS)

    file_IO_thread: threading.Thread = threading.Thread(target=file_IO_looper)
    file_IO_thread.start()
    print('file io thread started')

    def processing_looper(in_queue: Queue, err_queue: Queue, out_queue: Queue, settings: Settings):
        print('processing looper: started')

        while True:
            image: PIL.Image.Image|None = in_queue.get()

            # if receive fin flag, processing complete
            if image is None:
                # put fin flag into output queue to let other threads know
                out_queue.put(None)
                print('processing looper: recieved fin flag')
                return

            file_name:str = getattr(image, 'filename')
            assert file_name is not None
            print(f'processing received {file_name}')
            try:
                data = process_image(image, settings)

                out_name = Path(file_name).stem + '.jpg'

                # wait for a space in the output queue to put the image
                out_queue.put((out_name, data))
            # handle each processing-step's errors
            except compression.CompressionError as e:
                print(f'COMPRESSION error on file {file_name}: {e}')
                err_queue.put((image, e))
            # TODO: HANDLE ERRORS FROM ALL TYPES OF process-steps
            # generic error handling
            except Exception as e:
                print(f'UNEXPECTED Exception {e} Occurred')
                err_queue.put((image, e))

    # TODO: fix deadlock bug on final images from input queue
    subprocess_count = 1
    multiprocessing.set_start_method("fork", force=True)

    for i in range(subprocess_count):
        processing_thread: Process = Process(target=processing_looper, args=(in_queue, err_queue, out_queue, settings))
        processing_thread.start()
    print('processing process started')
            
## @brief saves an image that failed processing into the error folder and counts it as failed
def save_errored_image(image: PIL.Image.Image, err: Exception, err_dir: FolderManager) -> None:
    global stats_image_count_failed
    # TODO: save each type of processing-step error to a different dir
    try:
        file_name: str = getattr(image, 'filename')
        file_name = Path(file_name).stem + 'jpg'
        data: bytes = backup_get_image_data(image)
        err_dir.write_file(file_name, data)
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