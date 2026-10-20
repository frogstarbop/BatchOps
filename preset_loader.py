import os
import sys
from pathlib import Path
import image_compression as compression
import cropping
import bg_replacer as background
import head_alignment
import configparser

# Presets written on first run.
DEFAULT_PRESETS = {
    "Default Compression": {
        "type": "compression",
        "max_file_size": "200000",
        "preferred_widths": "1600, 1200, 800",
        "min_height": "600",
        "quality": "85",
    },
    "Default Crop": {
        "type": "crop",
        "width_ratio": "4",
        "height_ratio": "5",
    },
    "Default Alignment": {
        "type": "alignment",
        "head_x": "0.5",
        "head_y": "0.85",
    },
    "Default Background": {
        "type": "background",
        "background_rgb": "255, 255, 255",
        "intensity": "natural",
        "white_pt": "0.0",
        "model_name": "u2net",
    },
}

## @brief Creates presets.ini with the defaults if this computer doesn't have one yet
def ensure_presets_file() -> None:
    if PRESETS_PATH.exists():
        return
    config = configparser.ConfigParser()
    config.read_dict(DEFAULT_PRESETS)
    with open(PRESETS_PATH, "w") as configfile:
        config.write(configfile)



APP_NAME = "BatchOps"

## @brief Folder for per-user data that survives restarts, including in a frozen build
def get_config_dir() -> Path:
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    folder = base / APP_NAME
    folder.mkdir(parents=True, exist_ok=True)
    return folder

PRESETS_PATH: Path = get_config_dir() / "presets.ini"
## @brief get a CompressionSettings object for a given preset
def get_compression_settings(config, preset_name):
    preset = config[preset_name]
    return compression.CompressionSettings(
        name = preset_name,
        max_file_size = preset.getint("max_file_size"),
        preferred_widths=[
            int(width.strip()) for width in preset ["preferred_widths"].split(",")
        ],
        min_height=preset.getint("min_height"),
        quality = preset.getint("quality")
    )

## @brief get a CroppingSettings object for a given preset
def get_cropping_settings(config, preset_name):
    preset = config[preset_name]
    return cropping.CroppingSettings(
        name = preset_name,
        width_ratio=preset.getint("width_ratio"),
        height_ratio=preset.getint("height_ratio")
    )

## @brief get a backgroundsettings object for a given preset
def get_background_settings(config, preset_name):
    preset = config[preset_name]
    return background.BackgroundSettings(
        name = preset_name,
        background_rgb= [
            int(value.strip()) for value in preset["background_rgb"].split(",")
        ],
        intensity = preset["intensity"],
        white_pt=preset.getfloat("white_pt", fallback=0.0),
        model_name=preset["model_name"]
    )

def get_head_alignment_settings(config, preset_name):
    preset = config[preset_name]
    return head_alignment.HeadAlignmentSettings(
        name = preset_name,
        head_x = preset.getfloat("head_x", fallback = 0.5),
        head_y = preset.getfloat("head_y", fallback = 0.85)
    )

LOADERS = {
    "compression": get_compression_settings,
    "crop": get_cropping_settings,
    "background": get_background_settings,
    "alignment": get_head_alignment_settings
}

## @brief get the settings object for any preset, based on its type in the config
#
# @raises ValueError if the preset is not in the config
# @raises NotImplementedError if the preset's type has no loader
def load_settings(config, preset_name):
    if preset_name not in config:
        raise ValueError(f"preset '{preset_name}' no longer exists")
    
    preset_type = config[preset_name].get("type")
    if preset_type not in LOADERS:
        raise NotImplementedError(f"Type {preset_type} is not currently supported")
    return LOADERS[preset_type](config, preset_name)