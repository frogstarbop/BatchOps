from compression import CompressionSettings

from dataclasses import dataclass

## @brief A container for all the settings for compressing an image
@dataclass
class Settings:
    compression_enabled: bool
    compression: CompressionSettings
    # TODO: head_alignment
    # TODO: cropping
    # TODO: bg_removal
    # TODO: input_folder?
    # TODO: output_folder?