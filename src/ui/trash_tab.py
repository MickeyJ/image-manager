from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGridLayout,
    QScrollArea,
    QApplication,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from pathlib import Path
import logging

from ..utils.file_ops import get_recursive_image_files, delete_trash
from .widgets import ClickableImageLabel


class TrashTab(QWidget):
    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = Path(image_folder)
        self.trash_folder = self.image_folder / "trash"
        self.trash_folder.mkdir(exist_ok=True)

        self.current_index = 0
        self.image_files = []
        self.initUI()
        self.load_images()

    def initUI(self):
        self.layout = QVBoxLayout()

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        # Scrollable image area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)

        # Delete all button
        self.delete_button = QPushButton("Delete All Trash")
        self.delete_button.clicked.connect(self.delete_all)
        self.delete_button.setStyleSheet(
            """
            QPushButton {
                background-color: #ff4444;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """
        )
        self.layout.addWidget(self.delete_button)

        self.setLayout(self.layout)

    def load_images(self):
        """Load images from trash folder"""
        self.image_files = list(get_recursive_image_files(self.trash_folder))
        self.display_images()
        self.update_status()

    def display_images(self):
        """Display trashed images"""
        # Clear current display
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        if not self.image_files:
            no_images = QLabel("Trash is empty")
            no_images.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_images, 0, 0)
            return

        # Display images in grid
        for i, img_path in enumerate(self.image_files):
            try:
                row, col = divmod(i, 3)
                image_frame = ClickableImageLabel(
                    self,
                    show_trash=False,
                    show_restore=True,
                    root_folder=self.image_folder,
                )
                pixmap = QPixmap(str(img_path))
                if pixmap.isNull():
                    continue
                image_frame.setPixmap(pixmap)
                image_frame.image_path = img_path
                self.grid_layout.addWidget(image_frame, row, col)
            except Exception as e:
                logging.error(f"Error displaying image {img_path}: {e}")

    def update_status(self):
        """Update status label"""
        count = len(self.image_files)
        self.status_label.setText(f"Images in trash: {count}")

    def delete_all(self):
        """Delete all images in trash"""
        if not self.image_files:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Permanently delete all images in trash?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if delete_trash(self.image_folder):
                self.load_images()

    def refresh_view(self):
        """Refresh the image display"""
        self.load_images()
        self.display_images()
        self.update_status()
