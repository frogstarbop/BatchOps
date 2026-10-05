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
    QProgressBar,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QTransform

from PIL import Image, ImageFilter
import processor
from multiprocess import Process
import threading # TODO: use subprocess instead

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
        sub_process = threading.Thread(target=processor.dummy_process)
        sub_process.start()
    

    def ui_connect(self):

        self.closeButton = self.findChild(QPushButton, "closeButton")
        self.buttons.append(self.closeButton)
        self.closeButton.clicked.connect(self.on_closeButton_clicked)

        self.progressBar: QProgressBar = self.findChild(QProgressBar, "progressBar")
        self.largeGear: QLabel = self.findChild(QLabel, "largeGearIcon")
        self.smallGear: QLabel = self.findChild(QLabel, "smallGearIcon")
        self.largeGearPixMap: QPixmap = QPixmap("bundled/gear_large.png")
        self.smallGearPixMap: QPixmap = QPixmap("bundled/gear_small.png")

        self.timeRemaining = self.findChild(QLabel, "timeRemainingLabel")

        self.statusText = self.findChild(QTextBrowser, "statusTextBrowser")

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_frame)
        self.update_timer.start(1000 / 30) # TODO: match monitor frame rate

        # ----------DEBUG--------------
        self.debugExit = self.findChild(QPushButton, "debugExit")
        self.debugExit.clicked.connect(self.on_debugExit_clicked)

    def get_status_text(self) -> str:
        total = processor.get_images_total()
        success = processor.get_images_success()
        failed = processor.get_images_failed()
        not_started = total - (success + failed)
        return f'Not Started:\t{not_started}\nSuccessful:\t{success}\nFailed:\t\t{failed}\nTotal:\t\t{total}'
    def get_time_remaining_text(self) -> str:
        time_left = processor.get_estimated_time_left()
        if time_left < 60:
            return f'{time_left} seconds'
        time_left /= 60
        if time_left < 60:
            return f'{time_left} minutes'
        time_left /= 60
        if time_left < 24:
            return f'{time_left} hours'
        return f'{time_left} days'
    def rotate_gears(self) -> None:
        angle = 3.0
        transform = QTransform().rotate(angle)
        rotated_pixmap = self.largeGearPixMap.transformed(transform, Qt.SmoothTransformation)
        self.largeGear.setPixmap(rotated_pixmap)

    ## @brief For polling processing progress and updating display
    def update_frame(self):
        percent = int( processor.get_progress() * 100)
        self.progressBar.setValue(percent)
        self.statusText.setPlainText(self.get_status_text())
        self.timeRemaining.setText(self.get_time_remaining_text())
        self.rotate_gears()
        self.repaint()
        print('updating ' + str(processor.get_images_success()))

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
