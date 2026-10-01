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



        self.PresetButton = self.findChild(QPushButton, "PresetButton")


        if self.PresetButton:
            self.PresetButton.clicked.connect(self.on_PresetButton_clicked)
            image_filters = "Images (*.png)"
        else:
            print("Error")

    def on_PresetButton_clicked(self):
        print("Preset Button Interaction")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
