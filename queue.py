from pathlib import Path
import queue
from folder_manager import FolderManager, FolderError

### BIG FYI!!! This will be put into processor.py, I simply wanted to test the absolute basics, going to merge them together in the morn.
### Simple FIFO queue using the queue package (which is compatible with multithreading!)

def process(in_dir: FolderManager, out_dir: FolderManager):
    in_dir.validate()
    out_dir.validate()

    # TODO: do processing on another thread
    in_queue = queue.Queue()
    out_queue = queue.Queue()

    # image: PIL.Image.Image

    for image in in_dir: 
        file_name = getattr(image, 'filename', None) 
        assert file_name is not None
        in_queue.put(file_name)

    while not in_queue.empty():
        file_name, image = in_queue.get()
        print("Image:", file_name, "is in the in queue!!!!! Pretend this has been processed.")
        out_queue.put((file_name, image))

    while not out_queue.empty():
        file_name, image = out_queue.get()
        out_dir.write_file(file_name, data)

in_dir = FolderManager('from', True)
out_dir = FolderManager('to', False)
print('out dir is input ' + str(out_dir.is_input))
in_dir.set_path('./tests/images/jpeg/outdoors')
out_dir.set_path('./tests/images/output')

try:
    process(in_dir, out_dir)
except FolderError as e:
    print('failed to process: folder error: ' + e.path + ' ' + str(e))


        


