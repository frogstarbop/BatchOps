import image_compression as compression
import cropping
import bg_replacer as background

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


LOADERS = {
    "compression": get_compression_settings,
    "crop": get_cropping_settings,
    "background": get_background_settings
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