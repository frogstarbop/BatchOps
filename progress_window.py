# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass

import os
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QTextBrowser,
    QProgressBar
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from PIL import Image, ImageFilter

class Widget (QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.buttons = []
        loader = QUiLoader()

        ui_path = os.path.join(os.path.dirname(__file__), "progress_window.ui")

        self.ui = loader.load(ui_path, self)

        self.ui_connect()

        if parent is not None:
            self.setGeometry(parent.rect())
        
        self.background = QLabel(self)
        self.background.setGeometry(self.rect())
        self.background.lower()

        if parent is not None:
            self.create_blurred_background(parent)
    

    def ui_connect(self):

        self.closeButton = self.findChild(QPushButton, "closeButton")
        self.buttons.append(self.closeButton)
        self.closeButton.clicked.connect(self.on_closeButton_clicked)

        self.progressBar = self.findChild(QProgressBar, "progressBar")

        self.timeRemaining = self.findChild(QLabel, "timeRemainingLabel")

        self.statusText = self.findChild(QTextBrowser, "statusTextBrowser")

        # ----------DEBUG--------------
        self.debugExit = self.findChild(QPushButton, "debugExit")
        self.debugExit.clicked.connect(self.on_debugExit_clicked)
        

    def on_closeButton_clicked(self):
        print("close button clicked")


    # ---------DEBUG----------------
    def on_debugExit_clicked(self):
        self.close()
    # ---------DEBUG----------------

    def create_blurred_background(self, parent):
        if parent is None:
            return
        
        pixmap = parent.grab()

        image = pixmap.toImage()

        image = image.convertToFormat(
            image.Format.Format_RGBA8888
        )

        width = image.width()
        height = image.height()

        ptr = image.bits()

        pil_image = Image.frombuffer(
            "RGBA",
            (width, height),
            ptr,
            "raw",
            "RGBA",
            0,
            1
        )

        pil_image = pil_image.filter(ImageFilter.GaussianBlur(15))

        data = pil_image.tobytes("raw", "RGBA")

        blurred_image = image.copy()

        blurred_image.bits()[:len(data)] = data
        blurred_pixmap = QPixmap.fromImage(blurred_image)

        
        self.background.setPixmap(blurred_pixmap)
        self.background.setScaledContents(True)
