from settings import Settings
from multiprocess import Process
from folder_manager import FolderManager, FolderError
import PIL.Image
import compression
import io
import time

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
    total_time = delta_time / progress
    time_left = total_time - delta_time
    return int(time_left)

### main section ###
## @brief Handles the high level process of the images
def process(settings: Settings, in_dir: FolderManager, out_dir: FolderManager):
    in_dir.validate()
    out_dir.validate()
    mark_start_time()
    stats_image_count_total = in_dir.__count_images()

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

## @brief The most simple way to get image data for saving to file
def backup_get_image_data(image: PIL.Image.Image) -> bytes:
    # create an in-memory byte buffer than can be written to and read from
    virtual_file: io.BytesIO = io.BytesIO()

    # encode image
    image.save(virtual_file, format='JPEG')

    data = virtual_file.getvalue()
    virtual_file.close()
    return data

### TEMPORARY TESTING SECTION ###
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

# dummy process for mini-demo with client
def dummy_process():
    global stats_image_count_total
    global stats_image_count_success
    global stats_image_count_failed

    mark_start_time()
    stats_image_count_total = 100
    stats_image_count_success = 0
    stats_image_count_failed = 0
    for i in range(100):
        stats_image_count_success += 1
        time.sleep(0.1)
        print('complete image: ' + str(stats_image_count_success))

# in_dir = FolderManager('from', True)
# out_dir = FolderManager('to', False)
# print('out dir is input ' + str(out_dir.is_input))
# in_dir.set_path('./tests/images/jpeg/outdoors')
# out_dir.set_path('./tests/images/output')

# try:
#     sub_process = Process(target=process, args=(settings, in_dir, out_dir))
#     sub_process.start()
#     # process(settings, in_dir, out_dir)
# except FolderError as e:
#     print('failed to process: folder error: ' + e.path + ' ' + str(e))

