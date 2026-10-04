from pathlib import Path
import io
import PIL.Image

# TODO: add tests
# TODO: double-check all function commenting explains parameters
# TODO: add progress indications

## @brief Some of the image types PIL accepts
# src: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
valid_image_filetypes: set[str] = set([
    # normally used
    'png',
    'jpg',
    'jpeg',

    # could potentially be used at some point
    'webp', # common webpage image format
            # TODO: add some way to check whether the webp is animated
    'bmp',  # bitmap
    'dib',  # bitmap, similar to bmp
    'psd',  # adobe photoshop
    'wmf',  # windows metafile
    'tga',  # raster image format, lossless or raw image data
    'tiff', # tagged image file format, lossless

    # explicitly not handling
    # (niche/out-of-scope)
    # ico   # windows program icons
    # cur   # windows cursor
    # fits  # astronomy, scientific data
    # ppm   # raster image filetype from the 80s (1/3)
    # pgm   # raster image filetype from the 80s (2/3)
    # pbm   # raster image filetype from the 80s (3/3)
    # blp   # basically only WoW
    # dds   # video game texture format
    # (any animated image type)
    # gif
    # avif
    # (any other not mentioned here)
])

## @brief Custom error type for when folder fails validation
class FolderError(Exception):
    def __init__(self, folder_path: str, error_msg: str):
        self.path = folder_path
        super().__init__(error_msg)

## @brief Custom error type for image I/O issues
class ImageIOError(Exception):
    def __init__(self, file_path: str, error_msg: str):
        self.image_path = file_path
        super().__init__(error_msg)

## @brief Handles the validation and direct filesystem I/O of the folders
#
# Can get the valid image files in the folder by iterating it, iterators don't
# require loading the whole filename list into memory
#
class FolderManager:
    def __init__(self, name: str, is_input: bool):
        self.path: Path | None = None
        self.name: str = name
        self.is_input: bool = is_input
        self.current_index: int = 0 # iterable state tracker
        self.iterator = None

    ## @brief Set this folder's path (relative and absolute allowed)
    def set_path(self, path: str):
        self.path = Path(path)

    ## @brief Checks through a folder and returns whether contains subdirs
    def __check_for_subdirs(self) -> bool:
        assert self.path is not None
        for file in self.path.iterdir():
            if not file.is_file():
                return True
        return False

    ## @brief Check that this folder is ready to be used, raise error if not
    def validate(self) -> None:
        if self.path is None:
            raise FolderError('(None)', 'no folder path set')

        if not self.path.exists():
            raise FolderError(self.path.name, 'folder does not exist')

        if self.path.is_file():
            raise FolderError(self.path.name, 'folder is a file')

        if self.is_input:
            if self.__count_images() == 0:
                raise FolderError(self.path.name, 'folder does not contain any images to process')
        else:
            if self.__count_images() > 0:
                raise FolderError(self.path.name, 'folder already contains images')

        if self.__check_for_subdirs():
            raise FolderError(self.path.name, 'folder contains sub-folders')

    def __get_file_type(self, file_path: Path) -> str:
        return file_path.name.split('.')[-1]

    ## @brief Get the image count in the path
    #
    # THIS DOES NOT VALIDATE THE PATH FIRST! MAY RAISE ERRORS IF INVALID PATH
    #
    # @returns The number of valid images in this folder's path
    def __count_images(self) -> int:
        assert self.path is not None
        count: int = 0
        for file_path in self.path.iterdir():
            if not self.__get_file_type(file_path) in valid_image_filetypes:
                continue # ignore non-image types
            count += 1
        return count

    # TODO: make accept data as io.ReadableStream
    ## @brief Writes some bytes to a given file_name in this folder
    def write_file(self, file_name: str, data: bytes) -> None:
        assert self.path is not None
        # file_name might be naughty and have a relative filepath
        file_name = file_name.split('/')[-1]

        file_path = Path.joinpath(self.path, file_name)

        # open writer in exclusive-creation (x) for bytes (b), with buffering
        writer: io.BufferedWriter = open(file_path, 'xb', 1)

        writer.write(data)
        writer.close()

    ## @brief Iterator wrapper for internal Path instance
    def __iter__(self):
        assert self.path is not None
        self.iterator = self.path.iterdir()
        return self

    ## @brief Iterator wrapper for internal Path instance, read file as image
    def __next__(self) -> PIL.Image.Image:
        assert self.iterator is not None
        for file_path in self.iterator:
            if not self.__get_file_type(file_path) in valid_image_filetypes:
                continue
            return PIL.Image.open(file_path.as_posix(), 'r')

        raise StopIteration
