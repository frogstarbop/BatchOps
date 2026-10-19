from pathlib import Path

import mediapipe as mp
import numpy as np
from PIL import Image
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import FaceDetector, FaceDetectorOptions


## @brief Creates a MediaPipe face detector
#
# The model file must already be on disk, nothing is downloaded. The caller owns the
# detector and should close() it when finished. It is loaded once and reused so that
# many images can be processed without reloading the model.
#
# @param model_path Path to a BlazeFace .tflite model file
# @param min_confidence Detections scoring below this are ignored (0.0-1.0)
# @returns A face detector to pass to centre_face()
# @raises FileNotFoundError If there is no model file at model_path
def create_face_detector(
        model_path: Path = Path(__file__).with_name("blaze_face_full_range.tflite"),
        min_confidence: float = 0.35
) -> FaceDetector:
    if not model_path.exists():
        raise FileNotFoundError(f"face detection model not found at {model_path}")

    options = FaceDetectorOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        min_detection_confidence=min_confidence,
    )
    return FaceDetector.create_from_options(options)


## @brief Locates the most likely face and returns its centre coordinates
#
# If multiple faces are detected, the one with the highest confidence score is selected.
# This handles false positives that can occur when using a low minimum confidence threshold,
# which is necessary to pick up side-on and backwards shots of a person.
#
# @param image_array The (H, W, 3) RGB image to search
# @param detector A face detector, created by create_face_detector()
# @returns The (x, y) coordinates of the most confident face's centre in pixels
# @raises ValueError If no faces are found
def locate_face_centre(image_array: np.ndarray, detector: FaceDetector) -> tuple[float, float]:
    image_h, image_w = image_array.shape[:2]
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_array)
    detections = detector.detect(mp_image).detections

    if not detections:
        raise ValueError("Expected at least 1 face, found 0")

    best_detection = max(detections, key=lambda d: d.categories[0].score)

    box = best_detection.bounding_box

    left, top = max(box.origin_x, 0), max(box.origin_y, 0)
    right, bottom = min(box.origin_x + box.width, image_w), min(box.origin_y + box.height, image_h)

    return (left + right) / 2.0, (top + bottom) / 2.0


## @brief Calculates the target frame for the output image
#
# The frame keeps the original aspect ratio and its bottom edge always sits on the
# bottom of the original image, so the frame only ever extends above and beside it.
#
# @param image_size The (width, height) of the original photo in pixels
# @param face_centre The (x, y) of the face centre in pixels
# @param face_x Horizontal face placement as a fraction of output width
# @param face_y Vertical face placement as a fraction of output height from bottom
# @returns The target frame as (left, top, width, height) in original image coordinates
# @raises ValueError If the face is too close to the bottom to frame without padding underneath
def compute_target_frame(
        image_size: tuple[int, int],
        face_centre: tuple[float, float],
        face_x: float,
        face_y: float
) -> tuple[int, int, int, int]:
    image_w, image_h = image_size
    centre_x, centre_y = face_centre

    frame_h = (image_h - centre_y) / face_y
    frame_w = frame_h * image_w / image_h

    if min(frame_w, frame_h) < 1:
        raise ValueError("Face is too close to bottom to place at this height without padding underneath.")

    frame_left = round(centre_x - face_x * frame_w)
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


## @brief Re-frames a portrait so the primary face sits at a fixed position, extending the background
#
# The most likely face is found with MediaPipe to account for false positives at low confidence
# thresholds (needed for side-on and backwards shots), and the photo is re-framed with the same
# aspect ratio. Background is seamlessly reflected above and beside the person where needed,
# never underneath.
#
# @param image The portrait to process, already upright
# @param detector A face detector, created by the caller with create_face_detector()
# @param face_x Horizontal face placement as a fraction of output width (default 0.5)
# @param face_y Vertical face placement as a fraction of output height from bottom (default 0.85)
# @returns The new RGB PIL image, with the same aspect ratio as the input
# @raises ValueError If no faces are found, or the face is too low to frame
def centre_face(
        image: Image.Image,
        detector: FaceDetector,
        face_x: float = 0.5,
        face_y: float = 0.85,
) -> Image.Image:
    # FIX: Shave 2 pixels off the perimeter to destroy any edge artifacts (like a microscopic
    # white border or sharpening halo) before it gets mathematically reflected.
    width, height = image.size
    image = image.crop((2, 2, width - 2, height - 2))

    image_array = np.asarray(image.convert("RGB"))

    # Extract width and height straight from the array shape (H, W, Channels)
    image_size = (image_array.shape[1], image_array.shape[0])

    face_centre = locate_face_centre(image_array, detector)
    frame = compute_target_frame(image_size, face_centre, face_x, face_y)

    return reframe(image_array, frame)