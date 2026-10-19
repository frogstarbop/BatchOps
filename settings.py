from image_compression import CompressionSettings
from bg_replacer import BackgroundSettings
from cropping import CroppingSettings

from dataclasses import dataclass

# TEMPORARY PLACEHOLDERS
@dataclass
class HeadAlignmentSettings:
    beans: int

## @brief A container for all the settings for compressing an image
@dataclass
class Settings:
    compression_enabled: bool
    compression: CompressionSettings | None

    head_alignment_enabled: bool
    head_alignment: HeadAlignmentSettings | None

    cropping_enabled: bool
    cropping: CroppingSettings | None

    bg_removal_enabled: bool
    bg_removal: BackgroundSettings | None
