# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass


import sys
import os
import configparser
import compression
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QListWidget,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QListWidgetItem
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class Widget (QWidget):

    class PresetWidget (QWidget):
        def __init__(self, preset_name, settings, parent=None):
            super().__init__(parent)
            self.preset_name = preset_name
            self.settings = settings

            self.setup_widgets(preset_name, settings)

            self.setLayout(self.create_layout())



        def setup_widgets(self, preset_name, settings):
            self.nameLabel = QLabel(preset_name)

            self.maxFileSizeLabel = QLabel("max_file_size:")
            self.maxFileSizeSpinBox = QSpinBox()
            self.maxFileSizeSpinBox.setRange(0, 2147483647) # Max integer
            self.maxFileSizeSpinBox.setValue(settings.max_file_size)

            self.preferredWidthsLabel = QLabel("preferred_widths:")
            self.preferredWidthSpinBoxes = []
            for width in settings.preferred_widths:
                spinBox = QSpinBox()
                spinBox.setRange(0, 100000)
                spinBox.setValue(width)
                self.preferredWidthSpinBoxes.append(spinBox)


            self.minHeightLabel = QLabel("min_height:")
            self.minHeightSpinBox = QSpinBox()
            self.minHeightSpinBox.setRange(0,100000)
            self.minHeightSpinBox.setValue(settings.min_height)

            self.qualityLabel = QLabel("quality:")
            self.qualitySpinBox = QSpinBox()
            self.qualitySpinBox.setRange(0,100)
            self.qualitySpinBox.setValue(settings.quality)

        def create_layout(self):
            layout = QVBoxLayout()

            layout.addWidget(self.nameLabel)

            layout.addWidget(self.maxFileSizeLabel)
            layout.addWidget(self.maxFileSizeSpinBox)

            layout.addWidget(self.preferredWidthsLabel)

            for spinBox in self.preferredWidthSpinBoxes:
                layout.addWidget(spinBox)

            layout.addWidget(self.minHeightLabel)
            layout.addWidget(self.minHeightSpinBox)

            layout.addWidget(self.qualityLabel)
            layout.addWidget(self.qualitySpinBox)

            return layout


    buttons = []
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)

        self.config = configparser.ConfigParser()
        self.main_window = main_window
        loader = QUiLoader()
        ui_path = os.path.join(os.path.dirname(__file__), "edit_presets.ui")
        self.ui = loader.load(ui_path, self)


        self.presetsList = self.findChild(QListWidget, "presetsList")

        self.preset_path = os.path.join(
            os.path.dirname(__file__),
            "presets.ini"
        )


        if os.path.exists(self.preset_path):
            self.config.read(self.preset_path)

        self.load_presets()
        self.button_setup()


    def get_compression_settings(self, preset_name):
        preset = self.config[preset_name]

        return compression.CompressionSettings(
            max_file_size = preset.getint("max_file_size"),
            preferred_widths=[
                int(width) for width in preset["preferred_widths"].split(",")
            ],
            min_height = preset.getint("min_height"),
            quality = preset.getint("quality")
        )

    # ------------- Preset saving and loading ----------------------------------------

    def load_presets(self):
        for name in self.config.sections():
            settings = self.get_compression_settings(name)
            preset_widget = self.PresetWidget(name, settings)

            item = QListWidgetItem()
            item.setSizeHint(preset_widget.sizeHint())

            self.presetsList.addItem(item)
            self.presetsList.setItemWidget(item, preset_widget)

    def save_presets(self):
        with open(self.preset_path, "w") as configfile:
            self.config.write(configfile)

    # ------------- end preset saving and loading interaction methods ---------------------------------------

    # ---------------------- UI Setup Methods --------------------------------------------

    def button_setup(self):
        self.menuButton = self.findChild(QPushButton, "menuButton")
        self.buttons.append(self.menuButton)
        self.menuButton.clicked.connect(self.on_menuButton_clicked)

    # ---------------------- End UI Setup Methods ----------------------------------------


    # ------------- Button interaction methods -------------------------------------------

    def on_menuButton_clicked(self):
        print(self.main_window)
        self.close()
        self.main_window.show()

    # ------------- End Button interaction methods ----------------------------------------

    # ------------- Preset List modification methods --------------------------------------

    def add_compression_preset(self, name, settings):
        self.config[name] = {
            "max_file_size": str(settings.max_file_size),
            "preferred_widths": ",".join(
                str(width) for width in settings.preferred_widths
            ),
            "min_height": str(settings.min_height),
            "quality": str(settings.quality)
        }
        self.save_presets()
        self.load_presets()

    # ------------- End Preset List modification methods ----------------------------------

