# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass

import sys
import os
from PySide6.QtWidgets import(
    QApplication,
    QWidget,
    QPushButton
)
from PySide6.QtUiTools import QUiLoader

class Widget (QWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.buttons = []
        self.main_window = main_window
        loader = QUiLoader()
        ui_path = os.path.join(os.path.dirname(__file__), "credits.ui")
        self.ui = loader.load(ui_path, self)

        self.button_setup()

    def button_setup(self):
        self.menuButton = self.findChild(QPushButton, "menuButton")
        self.buttons.append(self.menuButton)
        self.menuButton.clicked.connect(self.on_menuButton_clicked)

    
    def on_menuButton_clicked(self):
        print(self.main_window)
        self.close()
        self.main_window.show()