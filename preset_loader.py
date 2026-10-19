import compression
import cropping
import background

def get_compression_settings(config, preset_name):
    preset = config[preset_name]
    return compression.CompressionSettings(
        name = preset_name,
        max_file_size = preset.getint("max_file_size"),
        preferred_widths = [int(w.strip()) for w in preset["preferred_widths"].split(",")],
        min_height = preset.getint("min_height"),
        quality = preset.getint("quality")
    )

def get_cropping_settings(config, preset_name):
    preset = config[preset_name]
    return cropping.CroppingSettings(
        name = preset_name,
        width_ratio = preset.getint("width_ratio"),
        height_ratio = preset.getint("height_ratio")
    )

def get_background_settings(config, preset_name):
    preset = config[preset_name]
    return background.BackgroundSettings(
        name = preset_name,
        background_rgb = [int(v.strip()) for v in preset["background_rgb"].split(",")],
        intensity = preset["intensity"],
        white_pt = preset.getfloat("white_pt"),
        model_name = preset["model_name"]
    )

LOADERS = {
    "compression": get_compression_settings,
    "crop": get_cropping_settings,
    "background": get_background_settings,
}

def load_settings(config, preset_type, preset_name):
    if preset_type not in LOADERS:
        raise ValueError(f"{preset_type} presets are not supported yet")
    if preset_name not in config:
        raise ValueError(f"preset '{preset_name}' no longer exists")
    return LOADERS[preset_type](config, preset_name)