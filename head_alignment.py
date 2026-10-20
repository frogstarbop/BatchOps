from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

from dataclasses import dataclass

@dataclass
class HeadAlignmentSettings:
    name: str
    head_x: float
    head_y: float

# Pose landmarks 0-10 are the head: nose, both eyes (inner/centre/outer), both ears and both mouth corners.
HEAD_LANDMARK_INDICES = range(11)


## @brief Creates a MediaPipe pose landmarker
#
# The model file must already be on disk, nothing is downloaded. The caller owns the
# landmarker and should close() it when finished. It is loaded once and reused so that
# many images can be processed without reloading the model.
#
# @param model_path Path to a pose landmarker .task model file (lite, full or heavy)
# @param min_confidence Pose detections / presence scoring below this are ignored (0.0-1.0)
# @returns A pose landmarker to pass to centre_head()
# @raises FileNotFoundError If there is no model file at model_path
def create_pose_landmarker(
        model_path: Path = Path(__file__).with_name("pose_landmarker_full.task"),
        min_confidence: float = 0.75,
) -> PoseLandmarker:
    if not model_path.exists():
        raise FileNotFoundError(f"pose landmarker model not found at {model_path}")

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=RunningMode.IMAGE,
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
# @returns The (x, y) coordinates of the head's centre in pixels
# @raises ValueError If there is not exactly one person in the image
def locate_head_centre(image_array: np.ndarray, landmarker: PoseLandmarker) -> tuple[float, float]:
    image_h, image_w = image_array.shape[:2]
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_array)
    poses = landmarker.detect(mp_image).pose_landmarks

    if len(poses) != 1:
        raise ValueError(f"Expected exactly 1 person, found {len(poses)}")

    head = [poses[0][i] for i in HEAD_LANDMARK_INDICES]

    # Landmarks are normalised to [0, 1] but can fall slightly outside the image, so clamp
    xs: list[float] = [(lm.x or 0.0) * image_w for lm in head]
    ys: list[float] = [(lm.y or 0.0) * image_h for lm in head]

    left, top = max(min(xs), 0.0), max(min(ys), 0.0)
    right, bottom = min(max(xs), float(image_w)), min(max(ys), float(image_h))

    return (left + right) / 2.0, (top + bottom) / 2.0


## @brief Calculates the target frame for the output image
#
# The frame keeps the original aspect ratio and its bottom edge always sits on the
# bottom of the original image, so the frame only ever extends above and beside it.
#
# @param image_size The (width, height) of the original photo in pixels
# @param head_centre The (x, y) of the head centre in pixels
# @param head_x Horizontal head placement as a fraction of output width
# @param head_y Vertical head placement as a fraction of output height from bottom
# @returns The target frame as (left, top, width, height) in original image coordinates
# @raises ValueError If the head is too close to the bottom to frame without padding underneath
def compute_target_frame(
        image_size: tuple[int, int],
        head_centre: tuple[float, float],
        head_x: float,
        head_y: float
) -> tuple[int, int, int, int]:
    image_w, image_h = image_size
    centre_x, centre_y = head_centre

    frame_h = (image_h - centre_y) / head_y
    frame_w = frame_h * image_w / image_h

    if min(frame_w, frame_h) < 1:
        raise ValueError("Head is too close to bottom to place at this height without padding underneath.")

    frame_left = round(centre_x - head_x * frame_w)
    frame_h = round(frame_h)

    return frame_left, image_h - frame_h, round(frame_w), frame_h


## @brief Extends the background with reflection padding and crops to the target frame
#
# @param image_array An (H, W, 3) array of the original photo
# @param frame The target frame as (left, top, width, height) in original image coordinates
# @returns The final framed RGB image
def reframe(image_array: np.ndarray, frame: tuple[int, int, int, int]) -> Image.Image:
    image_h, image_w = image_array.shape[:2]
    frame_left, frame_top, frame_w, frame_h = frame

    # Only pad where the frame pokes outside the image (never at the bottom)
    pad_top = max(0, -frame_top)
    pad_left = max(0, -frame_left)
    pad_right = max(0, frame_left + frame_w - image_w)

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

    # FIX: Shave 2 pixels off the perimeter to destroy any edge artifacts (like a microscopic
    # white border or sharpening halo) before it gets mathematically reflected.
    width, height = image.size
    image = image.crop((2, 2, width - 2, height - 2))

    # TODO: dont create this every image
    landmarker = create_pose_landmarker()

    image_array = np.asarray(image.convert("RGB"))

    # Extract width and height straight from the array shape (H, W, Channels)
    image_size = (image_array.shape[1], image_array.shape[0])

    head_centre = locate_head_centre(image_array, landmarker)
    frame = compute_target_frame(image_size, head_centre, head_x, head_y)

    return reframe(image_array, frame)