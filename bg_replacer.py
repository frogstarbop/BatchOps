from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
import numpy as np
import PIL.Image
import PIL.ImageFilter
from memory_profiler import profile
from timer import function_timer

if TYPE_CHECKING:
    from rembg.sessions.base import BaseSession

## @brief A container for all the settings for replacing an image's background
@dataclass
class BackgroundSettings:
    name: str
# @param background_rgb The (red, green, blue) background colour, 0-255 each

    background_rgb: tuple[int, int, int]

    ## A key of SHADOW_PRESETS: soft, natural, deep or dramatic
    intensity: str

    ## The brightness treated as unshaded, estimated from the photo if None
    white_pt: float | None

    model_name: str


# --- Normalization & Image Bounds ---
MAX_PIXEL_VALUE = 255.0
NORM_MIN = 0.0  # Pure black in float format
NORM_MAX = 1.0  # Pure white in float format

# --- Shadow extraction ---
MASK_BACKGROUND_THRESHOLD = 0.05  # Mask values below this count as original background
WHITE_POINT_PERCENTILE = 95.0  # High percentile rather than max, to ignore noise/glare
SHADOW_BLUR_RADIUS = 1.0  # Gaussian blur in pixels to remove camera noise/JPEG grain

# --- Colour Space Conversion Constants (IEC 61966-2-1 Standard) ---
SRGB_TO_LINEAR_THRESHOLD = 0.04045
LINEAR_TO_SRGB_THRESHOLD = 0.0031308
SRGB_LINEAR_SLOPE = 12.92
SRGB_OFFSET = 0.055
SRGB_SCALE = 1.055
SRGB_GAMMA_EXPONENT = 2.4

# --- Grayscale Luminance Weights (Rec. 709 Standard for HD/Web) ---
LUMINANCE_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

# --- Presets: (black_pt, midtones) ---
SHADOW_PRESETS = {
    "soft": (0.00, 1.20),  # Lifts shadows for compositing onto bright backgrounds
    "natural": (0.00, 1.00),  # Preserves the unedited original camera shadow density
    "deep": (0.01, 0.75),  # Compresses midtones for richer shadows without hard clipping
    "dramatic": (0.04, 0.60),  # High-contrast contact shadows for textured outdoor floors
}
DEFAULT_INTENSITY = "natural"

# --- Hardware acceleration: ONNX Runtime execution providers ---
# Needs: pip install onnxruntime-openvino  (Intel CPUs and GPUs, any OS)
OPENVINO_PROVIDER = "OpenVINOExecutionProvider"

# Needs: pip install onnxruntime-directml  (any GPU on Windows)
DML_PROVIDER = "DmlExecutionProvider"
DML_DEVICE_ID = 0  # Which GPU DirectML uses; default is 0

# Plain ONNX Runtime CPU provider, always available
CPU_PROVIDER = "CPUExecutionProvider"

## @brief Builds the provider priority list for the requested hardware
#
# @param hardware "gpu" or "cpu"
# @returns A list of provider names or (name, options) tuples, in priority order
def _select_providers(hardware: str) -> list:
    import onnxruntime

    if hardware not in ("gpu", "cpu"):
        raise ValueError(f"device must be 'gpu' or 'cpu', got {hardware!r}")

    available = onnxruntime.get_available_providers()
    providers = []

    if hardware == "gpu":
        if OPENVINO_PROVIDER in available:
            providers.append((OPENVINO_PROVIDER, {"device_type": "GPU"}))
        if DML_PROVIDER in available:
            providers.append((DML_PROVIDER, {"device_id": DML_DEVICE_ID, "arena_extend_strategy": "kSameAsRequested"}))
        if not providers:
            print("No GPU provider available, falling back to CPU")

    # CPU requested, or no GPU provider was found
    if not providers and OPENVINO_PROVIDER in available:
        providers.append((OPENVINO_PROVIDER, {"device_type": "CPU"}))

    providers.append(CPU_PROVIDER)
    return providers

## @brief Creates a rembg session that runs on the requested device
#
# Create this once and pass it to process() for every image, since loading the model is slow
# and uses a lot of memory.
#
# @param model_name The rembg model to load
# @param hardware "gpu" or "cpu"; falls back to the best available option if the preferred one isn't installed
# @returns A rembg session using the providers from _select_providers
def create_session(model_name: str, hardware: str) -> BaseSession:
    import onnxruntime
    import rembg

    providers = _select_providers(hardware)
    print(f"Using providers: {providers}")

    # Memory-saving options
    sess_opts = onnxruntime.SessionOptions()
    sess_opts.enable_mem_pattern = False  # don't pre-plan and hold one big block of memory
    sess_opts.enable_cpu_mem_arena = False  # give CPU memory back instead of caching it

    rembg_session = rembg.new_session(model_name, sess_opts=sess_opts, providers=providers)
    return rembg_session


## @brief Checks that a background colour is three values from 0-255
#
# @param background_rgb The (red, green, blue) colour to check
# @raises ValueError If the colour is not three values between 0 and 255
def validate_rgb(background_rgb: tuple[int, int, int]) -> None:
    if len(background_rgb) != 3:
        raise ValueError(f"background_rgb needs 3 values (r, g, b), got {len(background_rgb)}")
    for value in background_rgb:
        if not 0 <= value <= MAX_PIXEL_VALUE:
            raise ValueError(f"background_rgb values must be 0-255, got {value}")


## @brief Checks that an image has no transparent pixels
#
# An alpha channel that is fully opaque is accepted, since PNG, TIFF and TGA files are
# often saved as RGBA without using the transparency. Needs Pillow 10.1 or newer.
#
# @param image The image to check, in any mode
# @raises ValueError If any pixel is not fully opaque
def validate_opaque(image: PIL.Image.Image) -> None:
    # covers alpha channels (RGBA, LA, PA) and palette or colour-key transparency in image.info
    if not image.has_transparency_data:
        return

    # converting turns every kind of transparency into a real alpha channel to measure
    lowest_alpha = image.convert("RGBA").getchannel("A").getextrema()[0]
    if lowest_alpha < MAX_PIXEL_VALUE:
        raise ValueError("image has transparent pixels, flatten it to RGB before passing it in")


## @brief Converts an RGB PIL image into a 0.0-1.0 float array
#
# @param image An RGB PIL image
# @returns An (H, W, 3) float32 array in sRGB space
def image_to_array(image: PIL.Image.Image) -> np.ndarray:
    return np.array(image, dtype=np.float32) / MAX_PIXEL_VALUE


## @brief Converts a 0.0-1.0 float RGB array back into a PIL image
#
# @param array An (H, W, 3) float array in sRGB space
# @returns An RGB PIL image
def array_to_image(array: np.ndarray) -> PIL.Image.Image:
    pixels = np.round(np.clip(array, NORM_MIN, NORM_MAX) * MAX_PIXEL_VALUE)
    return PIL.Image.fromarray(pixels.astype(np.uint8))


## @brief Converts sRGB to Linear colour space for physically accurate blend math
#
# @param array Values in sRGB space (0.0-1.0)
# @returns The same shape in linear light
def srgb_to_linear(array: np.ndarray) -> np.ndarray:
    array = np.clip(array, NORM_MIN, NORM_MAX)
    # Dark values scale linearly to avoid infinite slope, brighter values follow a gamma curve
    return np.where(
        array <= SRGB_TO_LINEAR_THRESHOLD,
        array / SRGB_LINEAR_SLOPE,
        ((array + SRGB_OFFSET) / SRGB_SCALE) ** SRGB_GAMMA_EXPONENT,
    )


## @brief Converts Linear colour space back to sRGB for display and file export
#
# @param array Values in linear light (0.0-1.0)
# @returns The same shape in sRGB space
def linear_to_srgb(array: np.ndarray) -> np.ndarray:
    array = np.clip(array, NORM_MIN, NORM_MAX)
    return np.where(
        array <= LINEAR_TO_SRGB_THRESHOLD,
        array * SRGB_LINEAR_SLOPE,
        SRGB_SCALE * (array ** (1.0 / SRGB_GAMMA_EXPONENT)) - SRGB_OFFSET,
    )


## @brief Converts an RGB array to grayscale brightness
#
# @param fg_srgb An (H, W, 3) array in sRGB space
# @returns An (H, W) brightness array (0.0-1.0)
def to_luminance(fg_srgb: np.ndarray) -> np.ndarray:
    return np.dot(fg_srgb, LUMINANCE_WEIGHTS)


## @brief Remaps pixel intensities (Levels), blurs, and adjusts midtones to isolate shadows
#
# @param luminance An (H, W) grayscale array (0.0-1.0)
# @param black_pt The brightness that becomes pure black
# @param white_pt The brightness that becomes pure white, above black_pt and at most 1.0
# @param midtones Gamma for middle greys (1.0 leaves them unchanged)
# @param blur_radius Gaussian blur radius in pixels (0 disables)
# @returns An (H, W) array with the levels applied
# @raises ValueError If white_pt is not above black_pt or is above 1.0
def apply_levels(
    luminance: np.ndarray,
    black_pt: float,
    white_pt: float,
    midtones: float,
    blur_radius: float,
) -> np.ndarray:
    if not black_pt < white_pt <= NORM_MAX:
        raise ValueError(
            f"white_pt ({white_pt:.3f}) must be above black_pt ({black_pt:.3f}) and at most {NORM_MAX}, "
            "it is a 0-1 brightness, not 0-255. If it was estimated, "
            "the original background may be too dark to estimate shadows from"
        )

    adjusted = np.clip((luminance - black_pt) / (white_pt - black_pt), NORM_MIN, NORM_MAX)

    if blur_radius > 0:
        gray = PIL.Image.fromarray(np.round(adjusted * MAX_PIXEL_VALUE).astype(np.uint8))
        blurred = gray.filter(PIL.ImageFilter.GaussianBlur(radius=blur_radius))
        adjusted = np.array(blurred, dtype=np.float32) / MAX_PIXEL_VALUE

    return np.power(adjusted, 1.0 / midtones)


## @brief Estimates the white point from the brightness of the unshaded original background
#
# @param luminance An (H, W) brightness array of the original photo
# @param mask The (H, W) subject mask (1.0 = subject)
# @returns The estimated white point (0.0-1.0)
# @raises ValueError If the subject covers the whole frame so no background can be sampled
def estimate_white_point(luminance: np.ndarray, mask: np.ndarray) -> float:
    bg_pixels = luminance[mask < MASK_BACKGROUND_THRESHOLD]

    if bg_pixels.size == 0:
        raise ValueError("no background visible to estimate the white point from, pass white_pt explicitly")

    return float(np.percentile(bg_pixels, WHITE_POINT_PERCENTILE))


## @brief Cuts the subject out of an image using an AI matting model
#
# @param image The RGB image containing the subject
# @param session A rembg session, created by the caller with rembg.new_session()
# @returns An (H, W) float mask where 1.0 is subject and 0.0 is background
# @raises TypeError If session is not a rembg session, since rembg would silently load a default model
#                   for None and fail confusingly for anything else (such as a model name)
def extract_mask(image: PIL.Image.Image, session: BaseSession) -> np.ndarray:
    import rembg
    from rembg.sessions.base import BaseSession

    if not isinstance(session, BaseSession):
        raise TypeError(
            f"session must be created with rembg.new_session(<model name>), got {type(session).__name__}"
        )

    mask_image = rembg.remove(image, session=session, only_mask=True)
    return np.array(mask_image, dtype=np.float32) / MAX_PIXEL_VALUE


## @brief Looks up the black point and midtones of a shadow intensity preset
#
# @param intensity A key of SHADOW_PRESETS
# @returns The (black_pt, midtones) of the preset
# @raises ValueError If intensity is not a key of SHADOW_PRESETS
def get_shadow_preset(intensity: str) -> tuple[float, float]:
    if intensity not in SHADOW_PRESETS:
        raise ValueError(f"intensity must be one of {list(SHADOW_PRESETS)}, got '{intensity}'")

    return SHADOW_PRESETS[intensity]


## @brief Places the masked subject over a solid colour darkened by the shadow map
#
# @param fg_srgb The (H, W, 3) original photo in sRGB space
# @param mask The (H, W) subject mask (1.0 = subject)
# @param shadow_map_srgb The (H, W) shadow map in sRGB space
# @param background_rgb The (red, green, blue) background colour, 0-255 each
# @returns The (H, W, 3) composite in sRGB space
def composite(
    fg_srgb: np.ndarray,
    mask: np.ndarray,
    shadow_map_srgb: np.ndarray,
    background_rgb: tuple[int, int, int],
) -> np.ndarray:
    fg_lin = srgb_to_linear(fg_srgb)
    mask = mask[..., np.newaxis]
    shadow_map_lin = srgb_to_linear(shadow_map_srgb)[..., np.newaxis]

    bg_srgb = np.array(background_rgb, dtype=np.float32) / MAX_PIXEL_VALUE
    bg_lin = srgb_to_linear(bg_srgb)

    # Multiply blend: shadows darken the background, unshaded (white) areas leave it unchanged
    bg_darkened = bg_lin * shadow_map_lin

    final_lin = (fg_lin * mask) + (bg_darkened * (1.0 - mask))
    return linear_to_srgb(final_lin)


## @brief Replaces an image's background with a solid colour, keeping the original shadows
#
# @param image The portrait to process, already upright (EXIF rotation is not applied here)
# @param settings The background removal settings to apply
# @param session A rembg session from create_session(), required so the model is loaded once, not per image
# @returns The new RGB image, same size as the input
# @raises ValueError If the colour is invalid, the image has transparency, intensity is unknown,
#                    or white_pt cannot be estimated or is not above the preset's black point
#                    and at most 1.0
# @raises TypeError If session is not a rembg session

@function_timer()
@profile()
def process(image: PIL.Image.Image,
            settings: BackgroundSettings,
            session: BaseSession,
            ) -> PIL.Image.Image:
    from rembg.sessions.base import BaseSession

    # 1. A session must be provided, created once by the caller with create_session()
    if not isinstance(session, BaseSession):
        raise TypeError(
            f"session must be created with bg_replacer.create_session(<model name>), got {type(session).__name__}"
        )

    background_rgb: tuple[int, int, int] = settings.background_rgb
    intensity: str = settings.intensity
    white_pt: float | None = settings.white_pt

    # The preset editor can't store None, so 0 (or less) means estimate from photo
    if white_pt is not None and white_pt <= 0:
        white_pt = None

    validate_rgb(background_rgb)
    validate_opaque(image)
    # looked up now so a bad intensity fails before the slow matting step
    black_pt, midtones = get_shadow_preset(intensity)

    rgb_image = image.convert("RGB")
    fg_srgb = image_to_array(rgb_image)
    mask = extract_mask(rgb_image, session)

    luminance = to_luminance(fg_srgb)
    if white_pt is None:
        white_pt = estimate_white_point(luminance, mask)

    shadow_map_srgb = apply_levels(luminance, black_pt, white_pt, midtones, SHADOW_BLUR_RADIUS)
    final_srgb = composite(fg_srgb, mask, shadow_map_srgb, background_rgb)

    return array_to_image(final_srgb)