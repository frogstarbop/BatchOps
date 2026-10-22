from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions

from dataclasses import dataclass

@dataclass
class HeadAlignmentSettings:
    name: str
    head_x: float
    head_y: float

## @brief Creates a MediaPipe pose landmarker
# This is the model that is used to find a person from an image,
# creating landmark points that can be used to figure out the position of a head.
#
# @param model_path Path to a pose landmarker .task model file (lite, full or heavy)
# @param min_confidence Detections and presence scoring below this are ignored (0.0-1.0)
#
# @returns A pose landmarker to pass to process()
# @raises FileNotFoundError If there is no model file at model_path
def create_pose_landmarker(
        model_path:Path = Path(__file__).parent / "bundled" / "pose_landmarker_full.task",
        min_confidence: float = 0.75,
) -> PoseLandmarker:
    if not model_path.exists():
        raise FileNotFoundError(f"pose landmarker model not found at {model_path}")

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        num_poses=2,  # Only need to know whether there is more than one person
        min_pose_detection_confidence=min_confidence,
        min_pose_presence_confidence=min_confidence,
    )
    return PoseLandmarker.create_from_options(options)


## @brief Locates the head of the single person in the image and returns its centre coordinates
#
# The head's bounding box is the extent of the head landmarks (nose, eyes, ears, mouth).
#
# @param image_array The (H, W, 3) RGB image to search
# @param landmarker A pose landmarker, created by create_pose_landmarker()

# @returns The (x, y) coordinates of the head's centre the padded box around the whole person as (left, top, right, bottom)
# @raises ValueError If there is not exactly one person in the image
def calculate_head_coords(image_array: np.ndarray, landmarker: PoseLandmarker
                          ) -> tuple[tuple[float, float], tuple[float, float, float, float]]:
    image_h, image_w = image_array.shape[:2]

    # Mediapipe gets the pose landmarks
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_array)

    # Detect poses using media pipe on the image
    detection_result = landmarker.detect(mp_image)

    # List of detected pose landmark sets
    detected_poses = detection_result.pose_landmarks

    # Total count of detected poses
    num_poses = len(detected_poses)

    # Exactly one person must be present
    if num_poses != 1:
        # Raise error if 0 or multiple people are detected
        raise ValueError(f"Expected exactly 1 person, found {num_poses}")

    # Unpack the single pose list directly out of the 1-element detected_poses list
    [pose] = detected_poses

    # Slice the first 11 landmarks corresponding to facial features (indices 0-10)
    head_landmarks = pose[:11]

    # Convert normalized X coordinates (0.0 to 1.0) into absolute pixel coordinates
    landmark_x_coords: list[float] = [(lm.x or 0.0) * image_w for lm in head_landmarks]

    # Convert normalized Y coordinates (0.0 to 1.0) into absolute pixel coordinates
    landmark_y_coords: list[float] = [(lm.y or 0.0) * image_h for lm in head_landmarks]

    # Find max and min landmark coords
    box_left = min(landmark_x_coords)
    box_right = max(landmark_x_coords)
    box_top = min(landmark_y_coords)
    box_bottom = max(landmark_y_coords)

    # Return the centre coords
    x_center = (box_left + box_right) / 2.0
    y_center = (box_top + box_bottom) / 2.0


    # Below is to deal with reflecting the person

    # Box around every landmark (not just the head) so the whole body is covered
    body_x_coords = [(lm.x or 0.0) * image_w for lm in pose]
    body_y_coords = [(lm.y or 0.0) * image_h for lm in pose]

    # Add padding of 10% to the landmarks, since landmarks sit inside the body and miss hair, shoulders and clothing
    person_box_padding = 0.1

    # Horizontal and vertical padding, scaled by the width and height of the landmarks
    pad_x = (max(body_x_coords) - min(body_x_coords)) * person_box_padding
    pad_y = (max(body_y_coords) - min(body_y_coords)) * person_box_padding

    # Using the padding and the landmark coords create a padded box around the person to use for reflection validation
    person_box = (
        min(body_x_coords) - pad_x,
        min(body_y_coords) - pad_y,
        max(body_x_coords) + pad_x,
        max(body_y_coords) + pad_y,
    )
    return (x_center, y_center), person_box


## @brief Calculates the new image frame for the portrait's head to be centred
#
# The frame keeps the original aspect ratio and the new frames bottom edge always sits on the
# bottom of the original image, so the frame only ever extends above and beside it to accommodate original head position
#
# @param image_size The (width, height) of the original photo
# @param head_centre The (x, y) of the head centre
# @param head_x Horizontal head placement as a fraction of output width
# @param head_y Vertical head placement as a fraction of output height
#
# @returns The new image frame as (left, top, width, height) following rectangle convention of (x, y, w, h)
def compute_new_img_frame(
        image_size: tuple[int, int],
        head_centre: tuple[float, float],
        head_x: float,
        head_y: float
) -> tuple[int, int, int, int]:

    # width and height of the image provided
    image_w, image_h = image_size

    # the centre points of the head of the person in the image
    centre_x, centre_y = head_centre

    # calculate the vertical space between the bottom of the image and the head
    dist_between_bottom_and_head = image_h - centre_y

    # dist_between_bottom_and_head = head_y * frame_h
    # this formula means that head position should be head_y% up the new frame
    # we have the distance and head_y fraction so we can calculate the height of the new frame with substitution
    frame_h = round(dist_between_bottom_and_head / head_y)

    # image aspect ratio to keep
    img_ratio = image_w / image_h

    # scale width by the images aspect ratio
    frame_w = round(frame_h * img_ratio)

    # Distance from the frame's left edge to the head's centre
    # The head should sit head_x% of the way across the frame
    head_offset_x = head_x * frame_w

    # The head's centre is at centre_x in the original image, so the frame's left
    # edge is head_offset_x pixels to the left of it. This can be negative, which
    # means the frame pokes out past the left edge and needs padding.
    frame_left = round(centre_x - head_offset_x)

    # Gets the difference between the top of the original image and the new frame
    # This can be negative when the frame is taller than the image, which means it needs padding above.
    frame_top = image_h - frame_h

    # Standard rectangle convention for the new image frame (x, y, w, h)
    return frame_left, frame_top, frame_w, frame_h


## @brief Extends the background with reflection padding and crops to the target frame
#
# @param image_array An (H, W, 3) array of the original photo
# @param frame The new frame to extend the image array to fit
# @param person_box The padded box around the person as (left, top, right, bottom)

# @returns RGB image which has the head aligned
def extend_and_crop(
        image_array: np.ndarray,
        frame: tuple[int, int, int, int],
        person_box: tuple[float, float, float, float]
) -> Image.Image:

    image_h, image_w = image_array.shape[:2]

    frame_left, frame_top, frame_w, frame_h = frame
    person_left, person_top, person_right, person_bottom = person_box

    # Only add padding where the frame pokes outside the image (never at the bottom)
    pad_top = max(0, -frame_top)
    pad_left = max(0, -frame_left)
    pad_right = max(0, frame_left + frame_w - image_w)

    # Reflection copies the part of the photo next to each padded edge, flipped, into the new area.
    # If the person is inside that part of the photo, a mirrored copy of them would appear, so raise an error.
    if pad_top > 0 and person_top < pad_top:
        raise ValueError("Cannot extend the top: the reflection would mirror the person")
    if pad_left > 0 and person_left < pad_left:
        raise ValueError("Cannot extend the left: the reflection would mirror the person")
    if pad_right > 0 and person_right > image_w - pad_right:
        raise ValueError("Cannot extend the right: the reflection would mirror the person")

    padded_array = np.pad(
        image_array,
        pad_width=((pad_top, 0), (pad_left, pad_right), (0, 0)),
        mode="reflect"
    )

    # Padding on the top/left shifts the frame's origin into the padded array's coordinates
    crop_left = frame_left + pad_left
    crop_top = frame_top + pad_top

    return Image.fromarray(padded_array[crop_top: crop_top + frame_h, crop_left: crop_left + frame_w])


## @brief Re-frames a portrait so the head sits at a fixed position, extending the background
#
# The head is found with the MediaPipe pose landmarker, and the photo is re-framed with the same aspect ratio.
# Background is seamlessly reflected above and beside the person where needed, never underneath.
#
# @param image The portrait to process, already upright
# @param landmarker A pose landmarker, created by the caller with create_pose_landmarker()
# @param head_x Horizontal head placement as a fraction of output width (default 0.5)
# @param head_y Vertical head placement as a fraction of output height from bottom (default 0.85)
# @returns The new RGB PIL image, with the same aspect ratio as the input
# @raises ValueError If there is not exactly one person, or the head is too low to frame
def process(image: Image.Image, settings: HeadAlignmentSettings) -> Image.Image:
    head_x = settings.head_x
    head_y = settings.head_y

    # Shave 2 pixels off the perimeter to destroy any edge artifacts before the img gets reflected.
    width, height = image.size
    image = image.crop((2, 2, width - 2, height - 2))

    landmarker = create_pose_landmarker()

    image_array = np.asarray(image.convert("RGB"))

    # Extract width and height straight from the array shape (H, W, Channels)
    image_size = (image_array.shape[1], image_array.shape[0])

    head_coords, person_box = calculate_head_coords(image_array, landmarker)

    frame = compute_new_img_frame(image_size, head_coords, head_x, head_y)

    aligned_img = extend_and_crop(image_array, frame, person_box)

    return aligned_img