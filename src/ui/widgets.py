from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QProgressDialog,
    QApplication,
    QPushButton,
    QDialog,
    QWidget,
    QHBoxLayout,
    QSizePolicy,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize
import logging

from ..utils.file_ops import move_to_trash, restore_from_trash


class ExpandedImageWindow(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Viewer")
        self.setMinimumSize(800, 800)

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
    def __init__(
        self, parent=None, show_trash=True, show_restore=False, root_folder=None
    ):
        super().__init__(parent)
        self.root_folder = root_folder
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # Create button container for top corners
        self.button_container = QWidget(self)
        button_layout = QHBoxLayout(self.button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)

        # Create trash/restore button (left corner)
        if show_trash:
            self.trash_button = QPushButton("🗑", self)
            self.trash_button.setFixedSize(20, 20)
            self.trash_button.clicked.connect(self.move_to_trash)
            self.trash_button.setStyleSheet(self._get_button_style())
            button_layout.addWidget(self.trash_button)

        if show_restore:
            self.restore_button = QPushButton("↩", self)
            self.restore_button.setFixedSize(20, 20)
            self.restore_button.clicked.connect(self.restore_from_trash)
            self.restore_button.setStyleSheet(self._get_button_style())
            button_layout.addWidget(self.restore_button)

        # Add spacer to push expand button to right
        button_layout.addStretch()

        # Create expand button (right corner)
        self.expand_button = QPushButton("⤢", self)
        self.expand_button.setFixedSize(20, 20)
        self.expand_button.clicked.connect(self.show_expanded)
        self.expand_button.setStyleSheet(self._get_button_style())
        button_layout.addWidget(self.expand_button)

        # Set fixed height for button container
        self.button_container.setFixedHeight(30)

        # Create image container with proper constraints
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setMinimumSize(200, 200)

        # Add widgets to layout with proper constraints
        self.layout.addWidget(self.button_container, 0)  # Fixed height, no stretch
        self.layout.addWidget(self.image_label, 1)  # Gets remaining space

        self.setFixedSize(250, 250)  # Fix overall cell size
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)

        # Store original pixmap
        self.original_pixmap = None

        self.setStyleSheet(
            """
            ClickableImageLabel {
                background-color: white;
                margin: 5px;
            }
            ClickableImageLabel[selected="true"] {
                border: 2px solid red;
            }
        """
        )
        self.selected = False
        self.image_path = None

    def _get_button_style(self):
        return """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid gray;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 1.0);
            }
        """

    def setPixmap(self, pixmap):
        """Scale pixmap to fit the label while maintaining quality"""
        if not pixmap.isNull():
            self.original_pixmap = pixmap

            # Calculate available space for image
            available_height = (
                self.height() - self.button_container.height() - 10
            )  # Account for margins
            available_size = QSize(self.width() - 10, available_height)

            # Scale image to fit available space
            scaled_size = pixmap.size()
            scaled_size.scale(available_size, Qt.KeepAspectRatio)

            scaled_pixmap = pixmap.scaled(
                scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """Handle widget resize events with high quality scaling"""
        super().resizeEvent(event)
        if self.original_pixmap:
            self.setPixmap(self.original_pixmap)

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

    def move_to_trash(self):
        """Move image to trash folder"""
        if self.image_path:
            # Get root folder from parent tab if not provided
            root = self.root_folder
            if root is None and hasattr(self.parent(), "image_folder"):
                root = self.parent().image_folder

            success = move_to_trash(self.image_path, root)
            if success:
                parent = self.parent()
                while parent and not hasattr(parent, "refresh_view"):
                    parent = parent.parent()
                if parent and hasattr(parent, "refresh_view"):
                    parent.refresh_view()
            else:
                logging.error("Failed to move file - not updating UI")

    def restore_from_trash(self):
        """Restore image from trash"""
        if self.image_path:
            if restore_from_trash(self.image_path):
                parent = self.parent()
                while parent and not hasattr(parent, "refresh_view"):
                    parent = parent.parent()
                if parent and hasattr(parent, "refresh_view"):
                    parent.refresh_view()


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
