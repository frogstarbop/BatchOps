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
from PySide6.QtWidgets import (
        QApplication, 
        QWidget, 
        QPushButton, 
        QFileDialog, 
        QCheckBox, 
        QInputDialog,
        QScrollArea,
        QSizePolicy
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class Widget(QWidget):
        checkboxes = []
        buttons = []
        config = configparser.ConfigParser()
        config_preset_path = "presets.ini"

        def __init__(self, parent=None):
                config_preset_path = "presets.ini"
                super().__init__(parent)

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

                if os.path.exists(self.config_preset_path):
                        self.config.read(self.config_preset_path)
                        print("config exists")
                else:
                        with open(self.config_preset_path, "w") as configfile:
                                self.config.write(configfile)
                self.scrollArea = self.findChild(QScrollArea, "scrollArea")
                # Add buttons to program
                self.button_setup(self.buttons)

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

                # Add background presets button to class
                self.presetsBackground = self.findChild(QPushButton, "presetsBackground")
                buttons.append(self.presetsBackground)
                self.presetsBackground.clicked.connect(self.on_presetsBackground_clicked)

                # Add crop presets button to class
                self.presetsCrop = self.findChild(QPushButton, "presetsCrop")
                buttons.append(self.presetsCrop)
                self.presetsCrop.clicked.connect(self.on_presetsCrop_clicked)

                # Add compress presets button to class
                self.presetsCompress = self.findChild(QPushButton, "presetsCompress")
                buttons.append(self.presetsCompress)
                self.presetsCompress.clicked.connect(self.on_presetsCompress_clicked)

                # Add align presets button to class
                self.presetsAlign = self.findChild(QPushButton, "presetsAlign")
                buttons.append(self.presetsAlign)
                self.presetsAlign.clicked.connect(self.on_presetsAlign_clicked)

                # Add start button to class
                self.startButton = self.findChild(QPushButton, "startButton")
                buttons.append(self.startButton)
                self.startButton.clicked.connect(self.on_startButton_clicked)

                # Add credits button to class
                self.creditsButton = self.findChild(QPushButton, "creditsButton")
                buttons.append(self.creditsButton)
                self.creditsButton.clicked.connect(self.on_creditsButton_clicked)


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
                print("Select file button interaction")

        ## @brief Defines the interaction for the background preset button
        def on_presetsBackground_clicked(self):
                self.select_preset("background", self.presetsBackground)

        ## @brief Defines the interaction for the crop preset button
        def on_presetsCrop_clicked(self):
                self.select_preset("crop", self.presetsCrop)

        ## @brief Defines the interaction for the compress preset button
        def on_presetsCompress_clicked(self):
                self.select_preset("compression", self.presetsCompress)

        ## @brief Defines the interaction for the align preset button
        def on_presetsAlign_clicked(self):
                self.select_preset("alignment", self.presetsAlign)

        ## @brief Defines the interaction for the start button
        def on_startButton_clicked(self):
                print("start button clicked")

        ## @brief defines the interaction for the credits button
        def on_creditsButton_clicked(self):
                self.credits_window = CreditsWidget(self)
                self.credits_window.show()
                self.hide()

        # ------------- End Button interaction methods ----------------------------------------


        # ------------- Checkbox interaction methods ------------------------------------------

        ## @brief Defines the interaction for the background checkbox
        def on_checkboxBackground_stateChanged(self, state):
                print(f"Background check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                if(self.check_any_checkbox_states()):
                        self.startButton.setEnabled(True)
                else:
                        self.startButton.setEnabled(False)

        ## @brief Defines the interaction for the compress checkbox
        def on_checkboxCompress_stateChanged(self, state):
                print(f"Compress check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                if(self.check_any_checkbox_states()):
                        self.startButton.setEnabled(True)
                else:
                        self.startButton.setEnabled(False)

        ## @brief Defines the interaction for the crop checkbox
        def on_checkboxCrop_stateChanged(self, state):
                print(f"Crop check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                if(self.check_any_checkbox_states()):
                        self.startButton.setEnabled(True)
                else:
                        self.startButton.setEnabled(False)

        ## @brief Defines the interaction for the align checkbox
        def on_checkboxAlign_stateChanged(self, state):
                print(f"Align check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                if(self.check_any_checkbox_states()):
                        self.startButton.setEnabled(True)
                else:
                        self.startButton.setEnabled(False)

        # ------------- End Checkbox interaction methods ----------------------------------------
        
        ## brief select a preset of a particular type
        def select_preset(self, preset_type, button):

                # Get the list of preset names from the config file
                preset_names = [
                        name
                        for name in self.config.sections()
                        if self.config[name].get("type") == preset_type
                ]

                # insert a "None" option into the selection list (to leave room for custom non-preset operations)
                preset_names.insert(0, "None")
                
                # If no presets for the type...
                # In theory this never triggers, as None has been manually inserted
                if not preset_names:
                        print(f"No {preset_type} presets available")
                        return
                
                # Open a selection dialog for the presets
                preset_name, accepted = QInputDialog.getItem(
                        self,
                        "Select Preset",
                        "Preset:",
                        preset_names,
                        0,
                        False
                )

                # if the user closed the dialog and didn't select an option, then do not continue with the function
                if not accepted:
                        return

                # If None is selected then set the selected preset to None, update text appropriately
                if preset_name == "None":
                        self.selected_presets[preset_type] = None
                        button.setText("Current Preset: None")
                # Else if an option was selected, set the selected preset to the option, update the text appropriately
                else:
                        self.selected_presets[preset_type] = preset_name
                        button.setText(f"Current Preset: {preset_name}")

                # Update the scrollArea width based on the new button widths
                self.update_preset_area_width()
                print(f"selected {preset_type} preset: {preset_name}")

        ## @brief Update the scroll area width depending on the width of the buttons
        def update_preset_area_width(self):
                buttons = [
                self.presetsBackground,
                self.presetsCrop,
                self.presetsCompress,
                self.presetsAlign
                ]

                required_width = 200

                # update the required width based on the max width of a button
                for button in buttons:
                        required_width = max(
                                required_width,
                                button.sizeHint().width() + 20
                        )
                
                # Set the minimum width to the found required width
                self.scrollArea.setMinimumWidth(required_width)
                size_policy = self.scrollArea.sizePolicy()
                size_policy.setHorizontalPolicy(QSizePolicy.Policy.Preferred)
                self.scrollArea.setSizePolicy(size_policy)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
