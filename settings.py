from compression import CompressionSettings
from cropping import CroppingSettings
from background import BackgroundSettings

from dataclasses import dataclass

## @brief The settings for every processing step, a step is skipped when its settings are None
@dataclass
class Settings:
    compression: CompressionSettings | None = None
    cropping: CroppingSettings | None = None
    background: BackgroundSettings | None = None
    # TODO: head_alignment