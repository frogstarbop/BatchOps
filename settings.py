from compression import CompressionSettings
from cropping import CroppingSettings
from bg_replacer import BackgroundSettings
from dataclasses import dataclass

## @brief A container for all the settings for compressing an image
@dataclass
class Settings:
    compression_enabled: bool
    compression: CompressionSettings
    # TODO: head_alignment
    cropping_enabled: bool
    cropping: CroppingSettings
    bgrem_enabled: bool
    bgrem: BackgroundSettings
    # TODO: input_folder?
    # TODO: output_folder?