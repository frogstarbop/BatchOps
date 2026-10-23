from __future__ import annotations
import sys
import time 
import threading

if getattr(sys, "frozen", False):
    import types
    _matplotlib = types.ModuleType("matplotlib")
    _pyplot = types.ModuleType("matplotlib.pyplot")
    _matplotlib.pyplot = _pyplot
    sys.modules["matplotlib"] = _matplotlib
    sys.modules["matplotlib.pyplot"] = _pyplot

## This is a fix for a bug in PyInstaller that causes it to spawn a significant number of windows when doing the initial imports.
import multiprocessing 
multiprocessing.freeze_support()

import os
import configparser
from PySide6.QtWidgets import (
        QApplication,
        QProgressBar,
        QVBoxLayout, 
        QWidget, 
        QPushButton, 
        QFileDialog, 
        QCheckBox, 
        QScrollArea,
        QSizePolicy,
        QComboBox,
        QLabel,
        QMessageBox,
        QTextEdit
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer
from pathlib import Path
import shutil


progress = {"text" : "Starting..."}
_t0 = time.perf_counter()

## @brief On Linux, registers the app with the desktop (menu entry, icon, taskbar matching)
#
# Only runs from a packaged build. Rewrites the files each launch, so moving the
# executable just means starting it once from the new location.
def install_desktop_entry() -> None:

        # If the platform is not linux, then other methods work so return
        if not sys.platform.startswith("linux"):
                return

        data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

        icon_source = Path(__file__).parent / "bundled" / "logo.png"
        icon_dir = data_home / "icons" / "hicolor" / "256x256" / "apps"
        icon_dest = icon_dir / "batchops.png"
        if icon_source.exists():
                icon_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(icon_source, icon_dest)

        if getattr(sys, "frozen", False):
                exec_line = f'"{sys.executable}"'
        else:
                exec_line = f'"{sys.executable}" "{Path(__file__).resolve()}"'

        desktop_dir = data_home / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        (desktop_dir / "batchops.desktop").write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=BatchOps\n"
                f"Exec={exec_line}\n"
                f"Icon={icon_dest}\n"
                "Terminal=false\n"
                "Categories=Graphics;\n"
        )

class Widget(QWidget):
        checkboxes = []
        buttons = []
        selected_folder = ""
        config = configparser.ConfigParser()

        def __init__(self, parent=None):
                self.config_preset_path = str(preset_loader.PRESETS_PATH)
                super().__init__(parent)
                preset_loader.ensure_presets_file()
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

                self.outputFolderNameTextbox = self.findChild(QTextEdit, "outputFolderNameTb")
        
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
                        self.selected_folder or os.path.expanduser("~"),
                        QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog
                )

                if not folder:
                        return
                
                # Set the selected folder and input FolderManager to this folder
                self.selected_folder = folder
                self.in_dir.set_path(folder)

                # Set the output path to  be [folder]_processed in the same directory
                global input_path
                input_path = Path(folder)

                self.update_folder_label()

                self.scrollArea.setEnabled(True)
                self.update_start_enabled()
        
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
                global input_path

                # If the output folder name is empty, then show a warning and return
                if len(self.outputFolderNameTextbox.toPlainText()) < 1:
                        QMessageBox.warning(self, "You must select the name for your output folder", "You must enter a name for your output folder")
                        return

                self.out_dir.set_path(str(input_path.parent / f"{self.outputFolderNameTextbox.toPlainText()}"))

                # If the user has selected any checkboxes, then build the settings and process the images
                try:
                        settings = self.build_settings()
                except (ValueError, NotImplementedError) as error:
                        QMessageBox.warning(self, "Cannot start", str(error))
                        return

                # Validate the input and output folders before starting processing
                try:
                        self.in_dir.validate()
                        self.out_dir.validate()
                except FolderError as error:
                        QMessageBox.warning(self, "Folder problem", f"{error.path}: {error}")
                        return
                processor.process(settings, self.in_dir, self.out_dir)

                # Show the processing overlay
                self.processing_overlay = ProcessingWidget(self)
                self.processing_overlay.setGeometry(self.rect())
                self.processing_overlay.raise_()
                self.processing_overlay.show()

        ## @brief Enables or disables the start button based on whether a folder is selected and any checkboxes are checked
        def update_start_enabled(self):
                self.startButton.setEnabled(
                        self.in_dir.path is not None and self.check_any_checkbox_states()
                )

        ## @brief Builds the settings object based on the selected checkboxes and presets
        def build_settings(self):

                ## @brief Loads the settings for a particular step if its checkbox is checked
                def load_step(checkbox, preset_type, step_name):
                        # If the checkbox is not checked, return None as the step is not enabled
                        if checkbox.checkState() != Qt.CheckState.Checked:
                                return None
                        preset_name = self.selected_presets[preset_type]

                        # If the preset name is None, then raise an error as the user has not selected a preset for this step
                        if preset_name is None:
                                raise ValueError(f"select a {step_name} preset first")

                        # Else, load the settings for the selected preset and return it
                        return preset_loader.load_settings(self.config, preset_name)

                # Load the settings for each step if its checkbox is checked
                background = load_step(self.checkboxBackground, "background", "background removal")
                cropping = load_step(self.checkboxCrop, "crop", "crop")
                compression = load_step(self.checkboxCompress, "compression", "compression")
                alignment = load_step(self.checkboxAlign, "alignment", "head alignment")

                # If head alignment is enabled, check that the model file exists in the same folder as head_alignment.py
                if alignment is not None:
                        model_path = Path(head_alignment.__file__).parent / "bundled" / "pose_landmarker_full.task"
                        if not model_path.exists():
                                raise ValueError(
                                        f"Head alignment needs {model_path.name} "
                                        "in the same folder as head_alignment.py"
                                )

                # Return a Settings object with the loaded settings for each step
                return Settings(
                        compression_enabled = compression is not None,
                        compression = compression,
                        head_alignment_enabled = alignment is not None,
                        head_alignment=alignment,
                        cropping_enabled = cropping is not None,
                        cropping = cropping,
                        bg_removal_enabled= background is not None,
                        bg_removal=background
                )
       
        # ------------- End Button interaction methods ----------------------------------------


        # ------------- Checkbox interaction methods ------------------------------------------

        ## @brief Defines the interaction for the background checkbox
        def on_checkboxBackground_stateChanged(self, state):
                print(f"Background check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                self.update_start_enabled()

                if (state == Qt.CheckState.Checked):
                        self.presetsBackground.setEnabled(True)
                elif (state == Qt.CheckState.Unchecked):
                        self.presetsBackground.setEnabled(False)

        ## @brief Defines the interaction for the compress checkbox
        def on_checkboxCompress_stateChanged(self, state):
                print(f"Compress check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                self.update_start_enabled()

                if (state == Qt.CheckState.Checked):
                        self.presetsCompress.setEnabled(True)
                elif (state == Qt.CheckState.Unchecked):
                        self.presetsCompress.setEnabled(False)

        ## @brief Defines the interaction for the crop checkbox
        def on_checkboxCrop_stateChanged(self, state):
                print(f"Crop check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                self.update_start_enabled()

                if (state == Qt.CheckState.Checked):
                        self.presetsCrop.setEnabled(True)
                elif (state == Qt.CheckState.Unchecked):
                        self.presetsCrop.setEnabled(False)

        ## @brief Defines the interaction for the align checkbox
        def on_checkboxAlign_stateChanged(self, state):
                print(f"Align check state: {"Checked" if state == Qt.CheckState.Checked else "Unchecked"}")
                self.update_start_enabled()

                if (state == Qt.CheckState.Checked):
                        self.presetsAlign.setEnabled(True)
                elif (state == Qt.CheckState.Unchecked):
                        self.presetsAlign.setEnabled(False)

        # ------------- End Checkbox interaction methods ----------------------------------------
        def on_preset_changed(self, preset_type, preset_name):
                if not preset_name or preset_name == "None":
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

        ## @brief Override the resize event to adjust the processing overlay size
        def resizeEvent(self, event):
                super().resizeEvent(event)

                if self.processing_overlay is not None:
                        self.processing_overlay.setGeometry(self.rect())
        
        ## @brief Reloads the configuration from the preset file and repopulates the preset combo boxes
        def reload_config(self):
                self.config.clear()
                self.config.read(self.config_preset_path)

                self.populate_preset_combo(self.presetsBackground, "background")
                self.populate_preset_combo(self.presetsAlign, "alignment")
                self.populate_preset_combo(self.presetsCompress, "compression")
                self.populate_preset_combo(self.presetsCrop, "crop")

        ## @brief Opens the credits window and hides the main window
        def on_creditsLabel_linkActivated(self, link: str):
                from credits import Widget as CreditsWidget
                self.credits_window = CreditsWidget(self)
                self.credits_window.show()
                self.hide()
                
## @brief Creates a loading window with a progress bar and status label
def make_loading_window():
        window = QWidget()
        window.setWindowTitle("BatchOps")

        layout = QVBoxLayout(window)
        status_label = QLabel("Starting, please wait, this may take several minutes...")

        layout.addWidget(status_label)

        bar = QProgressBar()
        bar.setRange(0, 0)  # Indeterminate progress

        layout.addWidget(bar)
        window.setFixedSize(320, 100)
        window.show()
        return window, status_label

## @brief Reports a message to the console and updates the status label in the loading window
def report(text):
        print(f"[{time.perf_counter() - _t0:6.2f}s] {text}")
        progress["text"] = text

## @brief Loads the project modules in a separate thread to avoid blocking the UI
def load_project_modules():
        # Import the modules that are used in the project. This is done in a separate thread to avoid blocking the UI.
        global processor, preset_loader, head_alignment, Settings, FolderManager, FolderError, EditPresetsWidget, CreditsWidget, ProcessingWidget
        report ("Loading tools...")
        import processor
        import preset_loader
        import head_alignment
        from settings import Settings
        from folder_manager import FolderManager, FolderError

        report ("Loading windows...")
        from edit_presets import Widget as EditPresetsWidget
        from credits import Widget as CreditsWidget
        from progress_window import Widget as ProcessingWidget

        report ("Starting...")


if __name__ == "__main__":
        # Main entry point for the application. Sets up the QApplication, shows a loading window, and starts the main event loop.
        app = QApplication(sys.argv)
        app.setApplicationName("BatchOps")
        app.setDesktopFileName("batchops")
        app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "bundled", "logo.png")))

        # Create a loading window to show progress while the application is starting
        loading, status_label = make_loading_window()
        app.processEvents()  # Ensure the loading window is displayed

        # Close the splash screen if it exists (used when packaged with PyInstaller)
        try:
                import pyi_splash
                pyi_splash.close()
        except ImportError:
                pass

        # Start a separate thread to load the project modules, and handle any exceptions that occur during loading. 
        # The main thread periodically checks if the loading is complete and updates the UI accordingly.
        errors = []
        def import_thread():
                try:
                        load_project_modules()
                except BaseException as e:
                        errors.append(e)
        
        thread = threading.Thread(target=import_thread, daemon=True)
        thread.start()

        widget = None

        ## @brief Checks if the import thread has finished and updates the UI accordingly
        def finish_startup():
                ## If the import thread is still running, update the status label and return
                global widget
                status_label.setText(progress["text"])
                if thread.is_alive():
                        return

                ## If the import thread has finished, stop the timer and handle any errors that occurred during loading.
                timer.stop()
                if errors:
                        QMessageBox.critical(None, "BatchOps failed to start", repr(errors[0]))
                        app.quit()
                        return

                # If the import thread has finished successfully, set the multiprocessing start method to "spawn", install the desktop entry, create the main widget, and show it. 
                # Finally, close the loading window.
                multiprocessing.set_start_method("spawn", force=True)
                install_desktop_entry()
                widget = Widget()
                widget.show()
                loading.close()

        # Start a timer to periodically check if the import thread has finished. The timer will call finish_startup() every 50 milliseconds.
        timer = QTimer()
        timer.timeout.connect(finish_startup)
        timer.start(50)  # Check every 100 ms
        sys.exit(app.exec())
