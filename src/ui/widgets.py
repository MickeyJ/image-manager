from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QProgressDialog,
    QApplication,
    QPushButton,
    QDialog,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize


class ExpandedImageWindow(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Viewer")
        self.setMinimumSize(400, 400)

        layout = QVBoxLayout(self)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        # Load and display the image
        self.pixmap = QPixmap(str(image_path))
        self.update_image_size()

    def update_image_size(self):
        """Update image size when window is resized"""
        if not self.pixmap.isNull():
            scaled_pixmap = self.pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        self.update_image_size()


class ClickableImageLabel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.image_label = QLabel(self)

        # Create expand button
        self.expand_button = QPushButton("⤢", self)
        self.expand_button.setFixedSize(20, 20)
        self.expand_button.clicked.connect(self.show_expanded)
        self.expand_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid gray;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 1.0);
            }
        """
        )

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
        self.image_path = None

    def setPixmap(self, pixmap):
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

        # Position expand button in top-right corner
        button_margin = 5
        self.expand_button.move(
            self.width() - self.expand_button.width() - button_margin, button_margin
        )

    def resizeEvent(self, event):
        """Handle widget resize events"""
        super().resizeEvent(event)
        # Update expand button position
        if hasattr(self, "expand_button"):
            button_margin = 5
            self.expand_button.move(
                self.width() - self.expand_button.width() - button_margin, button_margin
            )

    def show_expanded(self):
        """Show the expanded image window"""
        if self.image_path:
            dialog = ExpandedImageWindow(self.image_path, self)
            dialog.exec_()

    def mousePressEvent(self, event):
        # Only toggle selection if not clicking the expand button
        if not self.expand_button.geometry().contains(event.pos()):
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
