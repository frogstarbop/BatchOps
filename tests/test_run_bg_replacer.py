import PIL.Image
import PIL.ImageOps
import os
import sys

# this makes the module to test importable
current_dir = os.path.dirname(os.path.abspath(__file__))
outer_dir = os.path.dirname(current_dir)
sys.path.append(outer_dir)

import bg_replacer

# constants
images_src_dir: str = 'images'
images_jpg_dir: str = os.path.join(images_src_dir, 'jpeg')
images_png_dir: str = os.path.join(images_src_dir, 'png')
images_output_dir: str = os.path.join(images_src_dir, 'output')

MODEL_NAME: str = "bria-rmbg"

natural_gray_preset = bg_replacer.BackgroundSettings(
    name = "natural_gray",
    background_rgb = (128, 128, 128),
    intensity = "natural",
    white_pt = None,
    model_name = MODEL_NAME,
)

dramatic_white_preset = bg_replacer.BackgroundSettings(
    name = "dramatic_white",
    background_rgb = (255, 255, 255),
    intensity = "dramatic",
    white_pt = None,
    model_name = MODEL_NAME,
)

presets = [natural_gray_preset, dramatic_white_preset]

# Takes files from the jpeg directory and outputs the result to the output directory
def background_test():
    # Ensure the output directory exists
    os.makedirs(images_output_dir, exist_ok=True)

    # Load the model once on the GPU and reuse it for every image
    session = bg_replacer.create_session(MODEL_NAME, "cpu")

    for filename in os.listdir(images_jpg_dir):

        input_path = os.path.join(images_jpg_dir, filename)
        output_path = os.path.join(images_output_dir, filename)

        # Skip subdirectories or non-file entries if any exist inside jpeg/
        if not os.path.isfile(input_path):
            continue

        try:
            # 'with' closes the file handle; each image is freed before the next loads
            with PIL.Image.open(input_path) as opened:
                image = PIL.ImageOps.exif_transpose(opened)

            # Process background replacement
            with bg_replacer.process(image, natural_gray_preset, session) as result:
                result.save(output_path)
            print(f"Processed: {filename}")

        except Exception as e:
            print(f"Skipped {filename}: {e}")


if __name__ == "__main__":
    background_test()