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
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap


class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Load the .ui file dynamically at runtime
        loader = QUiLoader()
        ui_path = os.path.join(os.path.dirname(__file__), "form.ui")
        self.ui = loader.load(ui_path, self)

        buttons = []


        # Add buttons to program
        self.button_setup(buttons)

        # Adding checkboxes to program...


    def button_setup(self, buttons: list[QPushButton]):
        # Adding buttons to program...
        self.presetButton = self.findChild(QPushButton, "PresetButton")
        buttons.append(self.presetButton)
        self.presetButton.clicked.connect(self.on_presetButton_clicked)

        self.selectFileButton = self.findChild(QPushButton, "selectFileButton")
        buttons.append(self.selectFileButton)
        self.selectFileButton.clicked.connect(self.on_selectFileButton_clicked)

        self.presetsBackground = self.findChild(QPushButton, "presetsBackground")
        buttons.append(self.presetsBackground)
        self.presetsBackground.clicked.connect(self.on_presetsBackground_clicked)

        self.presetsCrop = self.findChild(QPushButton, "presetsCrop")
        buttons.append(self.presetsCrop)
        self.presetsCrop.clicked.connect(self.on_presetsCrop_clicked)

        self.presetsCompress = self.findChild(QPushButton, "presetsCompress")
        buttons.append(self.presetsCompress)
        self.presetsCompress.clicked.connect(self.on_presetsCompress_clicked)

        self.presetsAlign = self.findChild(QPushButton, "presetsAlign")
        buttons.append(self.presetsAlign)
        self.presetsAlign.clicked.connect(self.on_presetsAlign_clicked)

        self.startButton = self.findChild(QPushButton, "startButton")
        buttons.append(self.startButton)
        self.startButton.clicked.connect(self.on_startButton_clicked)

    def on_presetButton_clicked(self):
        print("Preset Button Interaction")

    def on_selectFileButton_clicked(self):
        print("Select file button interaction")

    def on_presetsBackground_clicked(self):
        print("presets Background button clicked")

    def on_presetsCrop_clicked(self):
        print("presets crop clicked")

    def on_presetsCompress_clicked(self):
        print("presets compress clicked")

    def on_presetsAlign_clicked(self):
        print("presets align clicked")

    def on_startButton_clicked(self):
        print("start button clicked")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
