# This Python file uses the following encoding: utf-8

import sys
import os
import configparser
import compression
from dataclasses import fields
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
    QListWidgetItem,
    QDoubleSpinBox,
    QLineEdit
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class Widget (QWidget):
    buttons = []
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)

        # Set up the parser for the presets file
        self.config = configparser.ConfigParser()

        # Set the class's main window to be the passed main window
        self.main_window = main_window
        loader = QUiLoader()

        # figure out where the correct UI file is...
        ui_path = os.path.join(os.path.dirname(__file__), "edit_presets.ui")
        #... then load it
        self.ui = loader.load(ui_path, self)

        # Find and configure the presets listwidget
        self.presetsList = self.findChild(QListWidget, "presetsList")
        self.presetsList.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.presetsList.verticalScrollBar().setSingleStep(10)

        # find the preset config file
        self.preset_path = os.path.join(
            os.path.dirname(__file__),
            "presets.ini"
        )

        # If the preset config file exists, then read it
        if os.path.exists(self.preset_path):
            self.config.read(self.preset_path)

        # Load the presets from the file
        self.load_presets()

        # Connect the buttons on the form to the correct interaction functions
        self.button_setup()

    ## @brief get a CompressionSettings object for a given preset
    def get_compression_settings(self, preset_name):
        # Get the name of the preset from the configuration file
        preset = self.config[preset_name]

        # return the corresponding compressionSettings object based on the fields in the file
        return compression.CompressionSettings(
            max_file_size = preset.getint("max_file_size"),
            preferred_widths=[
                int(width) for width in preset["preferred_widths"].split(",")
            ],
            min_height = preset.getint("min_height"),
            quality = preset.getint("quality")
        )

    # ------------- Preset saving and loading ----------------------------------------

    # TODO: adjust this so that it is generic (doesn't just respond to CompressionSettings objects)
    ## @brief loads the presets into the listwidget
    def load_presets(self):
        # For each preset in the config file
        for name in self.config.sections():
            
            # Get the corresponding CompressionSettings object for this preset
            settings = self.get_compression_settings(name)
            # Create a PresetWidget from this preset
            preset_widget = PresetWidget(name, settings)

            item = QListWidgetItem()
            item.setSizeHint(preset_widget.sizeHint())

            # Add the preset widget to the listwidget
            self.presetsList.addItem(item)
            self.presetsList.setItemWidget(item, preset_widget)

    ## @brief save the presets back into the configfile
    def save_presets(self):
        with open(self.preset_path, "w") as configfile:
            self.config.write(configfile)

    # ------------- end preset saving and loading interaction methods ---------------------------------------

    # ---------------------- UI Setup Methods --------------------------------------------

    ## @brief connect all of the buttons to the correct interaction methods
    def button_setup(self):

        #Find and connect the main menu Button
        self.menuButton = self.findChild(QPushButton, "menuButton")
        self.buttons.append(self.menuButton)
        self.menuButton.clicked.connect(self.on_menuButton_clicked)

        # Find and connect the add preset button
        self.addPresetButton = self.findChild(QPushButton, "addPresetButton")
        self.buttons.append(self.addPresetButton)
        self.addPresetButton.clicked.connect(self.on_addPresetButton_clicked)

        # find and connect the remove preset button
        self.removePresetButton = self.findChild(QPushButton, "removePresetButton")
        self.buttons.append(self.removePresetButton)
        self.removePresetButton.clicked.connect(self.on_removePresetButton_clicked)

        # find and connect the save preset button
        self.savePresetButton = self.findChild(QPushButton, "savePresetButton")
        self.buttons.append(self.savePresetButton)
        self.savePresetButton.clicked.connect(self.on_savePresetButton_clicked)

    # ---------------------- End UI Setup Methods ----------------------------------------


    # ------------- Button interaction methods -------------------------------------------

    ## @brief sets up the interaction for the main menu button: closes this window and opens the main menu
    def on_menuButton_clicked(self):
        print(self.main_window)
        self.close()
        self.main_window.show()

    # TODO: implement add preset
    ## @brief adds a preset to the listwidget 
    def on_addPresetButton_clicked(self):
        print("add preset button clicked")

    # TODO: implement remove preset
    ## @brief removes a preset from the listwidget
    def on_removePresetButton_clicked(self):
        print("remove preset button clicked")

    # TODO: implement save preset
    ## @brief saves the current listwidget configuration state to the preset configuration file
    def on_savePresetButton_clicked(self):
        print("save preset button clicked")

    # ------------- End Button interaction methods ----------------------------------------

    # ------------- Preset List modification methods --------------------------------------

    ## @brief add a compression preset to the config
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

class PresetWidget (QWidget):
        def __init__(self, preset_name, settings, parent=None):
            super().__init__(parent)
            self.preset_name = preset_name
            self.settings = settings

            self.setting_widgets = {}

            # Figure out what widgets need to be inside the list
            self.setup_widgets(preset_name, settings)

            # Lay them out in the list widget
            self.setLayout(self.create_layout())


        ## @brief figures out which widgets are needed
        def setup_widgets(self, preset_name, settings):

            # Set up the name label widget
            self.nameLabel = QLabel(preset_name)
            font = self.nameLabel.font()
            font.setPointSize(20)
            font.setBold(True)
            self.nameLabel.setFont(font)

            # for each other field in settings, get the name and value and create a setting widget from it
            for field in fields(self.settings):
                setting_name = field.name
                value = getattr(self.settings, setting_name)
                editor = self.create_setting_widget(value)
                self.setting_widgets[setting_name] = editor

        ## @brief figure out what type of widget a field needs
        def create_setting_widget(self, value):
            # if its bool it needs a checkbox
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
                return widget

            # if int it needs custom int spinbox (doesn't change when scrolled)
            if isinstance(value, int):
                widget = NoScrollSpinBox()

                widget.setRange(0, 2147483647)
                widget.setValue(value)
                return widget

            # if float needs custom double spinbox (doesn't change when scrolled)
            if isinstance(value, float):
                widget = NoScrollDoubleSpinBox()

                widget.setRange(-2147483647, 2147483647)
                widget.setValue(value)
                return widget

            # if string it just needs an editable text field
            if isinstance(value, str):
                widget = QLineEdit()
                widget.setText(value)
                return widget

            # if its a list then create a listwidget from it
            if isinstance(value, list):
                return self.create_list_widget(value)

            # if its anything else then we can't do it (hopefully never triggers)
            raise TypeError(f"Unsupported preset setting type: {type(value).__name__}")

        ## @brief creates a list widget from a given value
        def create_list_widget(self, values):
            widget = QWidget()
            layout = QVBoxLayout(widget)

            editors = []

            # For each value in the list....
            for value in values:
                # if it is an integer, then create a custom int spinbox from it (doesn't change when scrolled)
                if isinstance(value, int):
                    editor = NoScrollSpinBox()
                    editor.setRange(0, 2147483647)

                    editor.setValue(value)

                    layout.addWidget(editor)

                    editors.append(editor)
                # otherwise we cannot do it
                else:
                    raise TypeError(f"Unsupported list value type: {type(value).__name__}")
            widget.editors = editors
            return widget

        ## @brief layout the widgets that were genereted by previous functions properly
        def create_layout(self):
            layout = QVBoxLayout()

            layout.addWidget(self.nameLabel)
            
            # for each field in settings...
            for field in fields(self.settings):
                # get the name of the field
                setting_name = field.name
                # get the corresponding generated widget
                editor = self.setting_widgets[setting_name]
                # Set the label
                label = QLabel(f"{setting_name}:")

                # add the label and the generated widget to the display
                layout.addWidget(label)
                layout.addWidget(editor)

            return layout

## @brief Custom SpinBox class so that the values can't be changed with scrolling
class NoScrollSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

## @brief custom double spinbox class so that the values can't be changed with scrolling
class NoScrollDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()
