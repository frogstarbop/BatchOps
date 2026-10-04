import PIL.Image
import io
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
outer_dir = os.path.dirname(current_dir)
sys.path.append(outer_dir)

import cropping

def cropping_test():
    if len(sys.argv) < 4:
        print("please file path as first argument e.g folder/test.img and aspect ratio as second and third argument e.g 4 3")
        sys.exit(1)
    
    image_path = sys.argv[1]
    width_ratio = int(sys.argv[2])
    height_ratio = int(sys.argv[3])

    image = PIL.Image.open(image_path)

    cropped_image = cropping.cropping(image, width_ratio, height_ratio)

    cropped_image.save('test_cropped_image.jpg')






if __name__ == "__main__":
    cropping_test()