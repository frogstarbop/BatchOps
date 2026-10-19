# # This Python file uses the following encoding: utf-8
# import sys

# from PySide6.QtWidgets import QApplication, QWidget

# # Important:
# # You need to run the following command to generate the ui_form.py file
# #     pyside6-uic form.ui -o ui_form.py, or
# #     pyside2-uic form.ui -o ui_form.py
# from ui_form import Ui_Widget

# class Widget(QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.ui = Ui_Widget()
#         self.ui.setupUi(self)


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     widget = Widget()
#     widget.show()
#     sys.exit(app.exec())
# widget.py
import sys
import os
import configparser
from edit_presets import Widget as EditPresetsWidget
from credits import Widget as CreditsWidget
from progress_window import Widget as ProcessingWidget
from folder_manager import FolderManager
from PySide6.QtWidgets import (
        QApplication, 
        QWidget, 
        QPushButton, 
        QFileDialog, 
        QCheckBox, 
        QInputDialog,
        QScrollArea,
        QSizePolicy,
        QComboBox,
        QLabel
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from pathlib import Path


class Widget(QWidget):
        checkboxes = []
        buttons = []
        selected_folder = ""
        config = configparser.ConfigParser()
        config_preset_path = "presets.ini"

        def __init__(self, parent=None):
                config_preset_path = "presets.ini"
                super().__init__(parent)
                self.in_dir = FolderManager("input", True)
                self.out_dir = FolderManager("output", False)
                self.comboBoxes = []
                self.processing_overlay = None

                # list of the current selected preset for each function
                self.selected_presets = {
                        "background": None,
                        "crop": None,
                        "compression": None,
                        "alignment": None
                }

                # Load the .ui file dynamically at runtime
                loader = QUiLoader()
                ui_path = os.path.join(os.path.dirname(__file__), "form.ui")
                self.ui = loader.load(ui_path, self)

                # If the config already exists, then read it, else create a config file
                if os.path.exists(self.config_preset_path):
                        self.config.read(self.config_preset_path)
                        print("config exists")
                else:
                        with open(self.config_preset_path, "w") as configfile:
                                self.config.write(configfile)

                self.scrollArea = self.findChild(QScrollArea, "scrollArea")
                # Add buttons to program
                self.button_setup(self.buttons)

                self.other_ui_setup()
                # Adding checkboxes to program...
                self.checkbox_setup(self.checkboxes)

                self.update_preset_area_width()

        ## @brief checks if any checkboxes are selected
        def check_any_checkbox_states(self):
                for checkbox in self.checkboxes:
                        if checkbox.checkState() == Qt.CheckState.Checked:
                                return True
                return False

        ## @brief save the current configuration to the file
        def save_current_configuration(self):
                with open(self.config_preset_path, "w") as configfile:
                        self.config.write(configfile)


        # ---------------------- UI Setup Methods --------------------------------------------

        def other_ui_setup(self):
                # Setup background preset selector
                self.presetsBackground = self.findChild(QComboBox, "presetsBackground")
                self.comboBoxes.append(self.presetsBackground)
                self.presetsBackground.currentTextChanged.connect(
                        lambda name: self.on_preset_changed("background", name)
                )
                
                # Setup crop preset selector
                self.presetsCrop = self.findChild(QComboBox, "presetsCrop")
                self.comboBoxes.append(self.presetsCrop)
                self.presetsCrop.currentTextChanged.connect(
                        lambda name: self.on_preset_changed("crop", name)
                )

                # Setup compress preset selector
                self.presetsCompress = self.findChild(QComboBox, "presetsCompress")
                self.comboBoxes.append(self.presetsCompress)
                self.presetsCompress.currentTextChanged.connect(
                        lambda name: self.on_preset_changed("compression", name)
                )

                # Setup align preset selector
                self.presetsAlign = self.findChild(QComboBox, "presetsAlign")
                self.comboBoxes.append(self.presetsAlign)
                self.presetsAlign.currentTextChanged.connect(
                        lambda name: self.on_preset_changed("alignment", name)
                )

                # Populate comboboxes
                self.populate_preset_combo(self.presetsBackground, "background")
                self.populate_preset_combo(self.presetsAlign, "alignment")
                self.populate_preset_combo(self.presetsCompress, "compression")
                self.populate_preset_combo(self.presetsCrop, "crop")

                # Setup credits page switcher
                self.creditsLabel = self.findChild(QLabel, "creditsLabel")
                self.creditsLabel.linkActivated.connect(self.on_creditsLabel_linkActivated)

                self.selectedFolderLabel = self.findChild(QLabel, "selectedFolderLabel")
        
        ## @brief populate a particular preset combo box with options
        def populate_preset_combo(self, combo, preset_type):

                # Get all preset names
                preset_names = [
                        name
                        for name in self.config.sections()
                        if self.config[name].get("type") == preset_type
                ]

                # Add the items to the presets and set the current index to be the placeholder
                combo.clear()
                combo.setPlaceholderText("Select a preset...")
                combo.addItems(preset_names)
                combo.setCurrentIndex(-1)
        ## @brief Connects all buttons in the GUI to their corresponding methods
        #
        # @param buttons The list of buttons on the form
        def button_setup(self, buttons: list[QPushButton]):
                # Adding buttons to program...

                # Add preset button to class
                self.presetButton = self.findChild(QPushButton, "PresetButton")
                buttons.append(self.presetButton)
                self.presetButton.clicked.connect(self.on_presetButton_clicked)

                # Add select file button to class
                self.selectFileButton = self.findChild(QPushButton, "selectFileButton")
                buttons.append(self.selectFileButton)
                self.selectFileButton.clicked.connect(self.on_selectFileButton_clicked)

                # Add start button to class
                self.startButton = self.findChild(QPushButton, "startButton")
                buttons.append(self.startButton)
                self.startButton.clicked.connect(self.on_startButton_clicked)


        ## @brief Connects all buttons in the GUI to their corresponding methods
        #
        # @param buttons The list of buttons on the form
        def checkbox_setup(self, checkboxes: list[QCheckBox]):
                # Add background checkbox to class
                self.checkboxBackground = self.findChild(QCheckBox, "checkBg")
                checkboxes.append(self.checkboxBackground)
                self.checkboxBackground.checkStateChanged.connect(self.on_checkboxBackground_stateChanged)

                # Add crop checkbox to class
                self.checkboxCrop = self.findChild(QCheckBox, "checkCrop")
                checkboxes.append(self.checkboxCrop)
                self.checkboxCrop.checkStateChanged.connect(self.on_checkboxCrop_stateChanged)

                # Add compress checkbox to class
                self.checkboxCompress = self.findChild(QCheckBox, "checkCompress")
                checkboxes.append(self.checkboxCompress)
                self.checkboxCompress.checkStateChanged.connect(self.on_checkboxCompress_stateChanged)

                # Add align checkbox to class
                self.checkboxAlign = self.findChild(QCheckBox, "checkAlign")
                checkboxes.append(self.checkboxAlign)
                self.checkboxAlign.checkStateChanged.connect(self.on_checkboxAlign_stateChanged)

        # ---------------------- End UI Setup Methods ----------------------------------------

        # ------------- Button interaction methods ------------------------------------------

        ## @brief Defines the interaction for the preset editor button
        def on_presetButton_clicked(self):
                self.edit_presets_window = EditPresetsWidget(self)
                self.edit_presets_window.show()
                self.hide()

        ## @brief Defines the interaction for the select file button
        def on_selectFileButton_clicked(self):
                
                # Select a folder with file dialog
                folder = QFileDialog.getExistingDirectory(
                        self,
                        "Select Folder",
                        self.selected_folder or os.path.expanduser("~")
                )

                if not folder:
                        return
                
                # Set the selected folder and input FolderManager to this folder
                self.selected_folder = folder
                self.in_dir.set_path(folder)

                # Set the output path to  be [folder]_processed in the same directory
                input_path = Path(folder)
                self.out_dir.set_path(str(input_path.parent / f"{input_path.name}_processed"))

                self.update_folder_label()

                self.scrollArea.setEnabled(True)
        
        ## @brief update the select folder label
        def update_folder_label(self):
                # Get the label
                label = self.selectedFolderLabel

                # shorten the path of the folder
                shortened = label.fontMetrics().elidedText(
                        self.selected_folder,
                        Qt.TextElideMode.ElideMiddle,
                        label.width()
                )
                # Set the label text to the shortened text
                label.setText(shortened)
                label.setToolTip(self.selected_folder)

        ## @brief Defines the interaction for the start button
        def on_startButton_clicked(self):
                self.processing_overlay = ProcessingWidget(self)

                self.processing_overlay.setGeometry(self.rect())
                self.processing_overlay.raise_()
                self.processing_overlay.show()

        # ------------- End Button interaction methods ----------------------------------------


        # ------------- Checkbox interaction methods ------------------------------------------

        ## @brief Defines the interaction for the background checkbox
        def on_checkboxBackground_stateChanged(self, state):
                print(f"Background check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                if(self.check_any_checkbox_states()):
                        self.startButton.setEnabled(True)
                else:
                        self.startButton.setEnabled(False)

                if (state == Qt.CheckState.Checked):
                        self.presetsBackground.setEnabled(True)
                elif (state == Qt.CheckState.Unchecked):
                        self.presetsBackground.setEnabled(False)

        ## @brief Defines the interaction for the compress checkbox
        def on_checkboxCompress_stateChanged(self, state):
                print(f"Compress check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                if(self.check_any_checkbox_states()):
                        self.startButton.setEnabled(True)
                else:
                        self.startButton.setEnabled(False)

                if (state == Qt.CheckState.Checked):
                        self.presetsCompress.setEnabled(True)
                elif (state == Qt.CheckState.Unchecked):
                        self.presetsCompress.setEnabled(False)

        ## @brief Defines the interaction for the crop checkbox
        def on_checkboxCrop_stateChanged(self, state):
                print(f"Crop check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                if(self.check_any_checkbox_states()):
                        self.startButton.setEnabled(True)
                else:
                        self.startButton.setEnabled(False)

                if (state == Qt.CheckState.Checked):
                        self.presetsCrop.setEnabled(True)
                elif (state == Qt.CheckState.Unchecked):
                        self.presetsCrop.setEnabled(False)

        ## @brief Defines the interaction for the align checkbox
        def on_checkboxAlign_stateChanged(self, state):
                print(f"Align check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                if(self.check_any_checkbox_states()):
                        self.startButton.setEnabled(True)
                else:
                        self.startButton.setEnabled(False)

                if (state == Qt.CheckState.Checked):
                        self.presetsAlign.setEnabled(True)
                elif (state == Qt.CheckState.Unchecked):
                        self.presetsAlign.setEnabled(False)

        # ------------- End Checkbox interaction methods ----------------------------------------
        def on_preset_changed(self, preset_type, preset_name):
                if preset_name == "None":
                        self.selected_presets[preset_type] = None
                else:
                        self.selected_presets[preset_type] = preset_name
                
                print(f"selected {preset_type} preset: {self.selected_presets[preset_type]}")

        ## @brief Update the scroll area width depending on the width of the buttons
        def update_preset_area_width(self):
                comboboxes = [
                self.presetsBackground,
                self.presetsCrop,
                self.presetsCompress,
                self.presetsAlign
                ]

                required_width = 200

                # update the required width based on the max width of a button
                for box in comboboxes:
                        required_width = max(
                                required_width,
                                box.sizeHint().width() + 20
                        )
                
                # Set the minimum width to the found required width
                self.scrollArea.setMinimumWidth(required_width)
                size_policy = self.scrollArea.sizePolicy()
                size_policy.setHorizontalPolicy(QSizePolicy.Policy.Preferred)
                self.scrollArea.setSizePolicy(size_policy)
        
        def resizeEvent(self, event):
                super().resizeEvent(event)

                if self.processing_overlay is not None:
                        self.processing_overlay.setGeometry(self.rect())
        
        def reload_config(self):
                self.config.clear()
                self.config.read(self.config_preset_path)

                self.populate_preset_combo(self.presetsBackground, "background")
                self.populate_preset_combo(self.presetsAlign, "alignment")
                self.populate_preset_combo(self.presetsCompress, "compression")
                self.populate_preset_combo(self.presetsCrop, "crop")
        
        def on_creditsLabel_linkActivated(self, link: str):
                self.credits_window = CreditsWidget(self)
                self.credits_window.show()
                self.hide()
                


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
