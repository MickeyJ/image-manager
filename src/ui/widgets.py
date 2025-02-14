from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QProgressDialog,
    QApplication,
    QPushButton,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class ClickableImageLabel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)

        self.layout.setAlignment(Qt.AlignCenter)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(200, 200)

        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet(
            """
            ClickableImageLabel {
                background-color: white;
                margin: 5px;
                padding: 5px;
            }
            ClickableImageLabel[selected="true"] {
                border: 2px solid red;
            }
        """
        )
        self.selected = False

    def setPixmap(self, pixmap):
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def mousePressEvent(self, event):
        self.selected = not self.selected
        self.setProperty("selected", self.selected)
        self.style().unpolish(self)
        self.style().polish(self)


class LoadingSpinner:
    def __init__(self, parent, text="Processing...", cancellable=False):
        self.progress = QProgressDialog(
            text, "Cancel" if cancellable else None, 0, 0, parent
        )
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setWindowTitle("Please Wait")
        self.progress.setMinimumDuration(0)
        self.progress.setAutoClose(True)
        self.progress.setMinimumWidth(400)  # Make dialog wider

        # Style the cancel button if present
        if cancellable:
            cancel_button = QPushButton("Cancel")
            cancel_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #ff4444;
                    color: white;
                    padding: 5px 15px;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #ff0000;
                }
            """
            )
            self.progress.setCancelButton(cancel_button)
            self.progress.canceled.connect(self.handle_cancel)

        self.cancelled = False

    def setLabelText(self, text):
        """Update the progress text"""
        self.progress.setLabelText(text)
        QApplication.processEvents()

    def show(self):
        self.progress.show()
        QApplication.processEvents()

    def close(self):
        self.progress.close()

    def handle_cancel(self):
        self.cancelled = True
        self.progress.setLabelText("Cancelling...")
        QApplication.processEvents()

    @property
    def was_cancelled(self):
        return self.cancelled
