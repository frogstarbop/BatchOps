
# this makes the module to test importable
import os
import sys
import PIL.Image
import PIL.ImageOps


current_dir = os.path.dirname(os.path.abspath(__file__))
outer_dir = os.path.dirname(current_dir)
sys.path.append(outer_dir)

import head_alignment

# constants
images_src_dir: str = 'images'
images_jpg_dir: str = os.path.join(images_src_dir, 'jpeg')
images_png_dir: str = os.path.join(images_src_dir, 'png')
images_failures_dir: str = os.path.join(images_src_dir, 'head_alignment_specific')
images_output_dir: str = os.path.join(images_src_dir, 'output')

standard_align_preset = head_alignment.HeadAlignmentSettings(
    head_x = 0.5,
    head_y = 0.85,
)


bad_reflect_preset = head_alignment.HeadAlignmentSettings(
    head_x = 0.5,
    head_y = 0.05,
)


presets = [standard_align_preset]
fail_presets = [bad_reflect_preset]

# Takes files from the jpeg directory and outputs the result to the output directory
def alignment_test():
    # Ensure the output directory exists
    os.makedirs(images_output_dir, exist_ok=True)

    with head_alignment.create_pose_landmarker() as landmarker:
        for filename in os.listdir(images_jpg_dir):

            input_path = os.path.join(images_jpg_dir, filename)
            output_path = os.path.join(images_output_dir, filename)

            # Skip subdirectories or non-file entries if any exist inside jpeg/
            if not os.path.isfile(input_path):
                continue

            try:
                image = PIL.Image.open(input_path)
                image = PIL.ImageOps.exif_transpose(image)

                # Process alignment
                result = head_alignment.process(image, standard_align_preset)
                result.save(output_path)
                print(f"Processed: {filename}")

            except Exception as e:
                print(f"Skipped {filename}: {e}")

if __name__ == "__main__":
    alignment_test()