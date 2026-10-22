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
    QMessageBox
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import (Qt, QTimer)
from PySide6.QtGui import (QPixmap, QMovie)

from PIL import Image, ImageFilter

import processor

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

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_frame)
        self.update_timer.start(1000 // 30) # TODO: match monitor frame rate

        self.rotate_gears()

    def ui_connect(self):

        self.closeButton = self.findChild(QPushButton, "closeButton")
        self.buttons.append(self.closeButton)
        self.closeButton.clicked.connect(self.on_closeButton_clicked)
        self.largeGear = self.findChild(QLabel, "gearIcon")

        self.progressBar = self.findChild(QProgressBar, "progressBar")

        self.timeRemaining = self.findChild(QLabel, "timeRemainingLabel")

        self.statusText = self.findChild(QTextBrowser, "statusTextBrowser")

    def on_closeButton_clicked(self):
        self.close()

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

    # ----------- PROGRESS INFO ----------
    def get_status_text(self) -> str:
        total = processor.get_images_total()
        success = processor.get_images_success()
        failed = processor.get_images_failed()
        not_started = total - (success + failed)
        return f'Not Started:\t{not_started}\nSuccessful:\t{success}\nFailed:\t\t{failed}\nTotal:\t\t{total}'

    def is_finished(self) -> bool:
        total = processor.get_images_total()
        done = processor.get_images_success() + processor.get_images_failed()
        return total > 0 and done >= total

    def get_time_remaining_text(self) -> str:
        time_left = processor.get_estimated_time_left()
        if time_left < 0:
            return 'Estimating...'
        if time_left < 60:
            return f'{time_left} seconds'
        time_left //= 60
        if time_left < 60:
            return f'{time_left} minutes'
        time_left //= 60
        if time_left < 24:
            return f'{time_left} hours'
        return f'{time_left} days'

    def rotate_gears(self) -> None:
        self.movie = QMovie('bundled/big_gear_rotating.gif')

        if not self.movie.isValid():
            print('UI Error: could not find gear')
            return

        # might want to scale later
        # self.movie.setScaledSize(QSize(300, 300))

        self.largeGear.setMovie(self.movie)
        self.movie.start()

    ## @brief For polling processing progress and updating display
    def update_frame(self):
        finished = self.is_finished()
        
        percent = int( processor.get_progress() * 100)
        self.progressBar.setValue(percent)
        self.statusText.setPlainText(self.get_status_text())
        
        if finished:
            if self.movie.isValid():
                self.movie.stop()
            self.update_timer.stop()
            self.timeRemaining.setText('Finished!')
            self.closeButton.setEnabled(True)
            QMessageBox.information(self, "Processing completed!", "Your images are ready!")
            return
        
        self.timeRemaining.setText(self.get_time_remaining_text())
        self.repaint()
    

