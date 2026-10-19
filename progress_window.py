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
import time
import threading # TODO: use subprocess instead

USE_DUMMY_PROCESSOR = False

class Widget (QWidget):
    def __init__(self, parent = None, settings=None, in_dir=None, out_dir=None):
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
        # sub_process = threading.Thread(target=processor.dummy_process)
        # sub_process.start()

        self.worker_error = None
        self.start_time = time.time()
        self.worker = threading.Thread(
            target = self.run_worker, args = (settings, in_dir, out_dir), daemon=True
        )
        self.worker.start()
    

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
        self.update_timer.start(1000 // 30) # TODO: match monitor frame rate

        # ----------DEBUG--------------
        self.debugExit = self.findChild(QPushButton, "debugExit")
        self.debugExit.clicked.connect(self.on_debugExit_clicked)

    def get_status_text(self) -> str:
        total = processor.get_images_total()
        success = processor.get_images_success()
        failed = processor.get_images_failed()
        not_started = total - (success + failed)
        
        
        # return f'Not Started:\t{not_started}\nSuccessful:\t{success}\nFailed:\t\t{failed}\nTotal:\t\t{total}'

        text = f'Not Started:\t{not_started}\nSuccessful:\t{success}\nFailed:\t\t{failed}\nTotal:\t\t{total}'
        if self.worker_error:
            text+= f'\n\nStopped early: {self.worker_error}'

        if hasattr(processor, 'get_errors'):
            errors = processor.get_errors()
            if errors: 
                text += '\n\nFailed: \n' + '\n'.join(errors)
        return text
    
    
    def get_time_remaining_text(self) -> str:
        
        progress = self.get_progress_fraction()

        if progress == 0:
            return "Estimating..."
        elapsed = time.time() - self.start_time

        seconds = int(elapsed / progress - elapsed)

        if seconds < 60:
            return f'{seconds} seconds'
        
        minutes = seconds // 60
        if minutes < 60:
            return f'{minutes} minutes'
        
        hours = minutes // 60
        if hours < 24:
            return f'{hours} hours'
        
        return f'{hours // 24} days'
    
    
    def rotate_gears(self) -> None:
        angle = 3.0
        transform = QTransform().rotate(angle)
        rotated_pixmap = self.largeGearPixMap.transformed(transform, Qt.SmoothTransformation)
        self.largeGear.setPixmap(rotated_pixmap)

    ## @brief For polling processing progress and updating display
    def update_frame(self):
        
        finished = not self.worker.is_alive()

        self.progressBar.setValue(int(self.get_progress_fraction() * 100))
        self.statusText.setPlainText(self.get_status_text())

        if finished:
            self.update_timer.stop()
            self.timeRemaining.setPlainText(self.get_status_text())

            self.closeButton.setEnabled(True)
            return
        
        self.timeRemaining.setText('Stopped' if self.worker_error else 'Finished')

        self.rotate_gears()


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
    
    def run_worker(self, settings, in_dir, out_dir):
        try:
            if USE_DUMMY_PROCESSOR:
                processor.dummy_process()
            else:
                processor.process(settings, in_dir, out_dir)
        except Exception as error:
            self.worker_error = str(error)

    def get_progress_fraction(self) -> float:
        total = processor.get_images_total()

        if total ==0:
            return 0.0
        return (processor.get_images_succcess() * processor.get_images_failed()) / total
