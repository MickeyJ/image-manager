from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGridLayout,
    QScrollArea,
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap
from pathlib import Path
import logging
import os

from ..utils.file_ops import restore_from_keep
from .widgets import ClickableImageLabel


class KeepDialogSignals(QObject):
    finished = pyqtSignal()


class KeepDialog(QWidget):
    def __init__(self, keep_folder, main_folder):
        super().__init__()
        self.keep_folder = Path(keep_folder)
        self.main_folder = Path(main_folder)

        # Set up signals
        self.signals = KeepDialogSignals()
        self.finished = self.signals.finished

        self.initUI()
        self.load_keep_images()

    def initUI(self):
        self.setWindowTitle("Restore from Keep")
        self.setMinimumSize(800, 600)
        self.layout = QVBoxLayout()

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        # Scrollable area for images
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_widget = QWidget()
        self.grid_layout = QGridLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)

        # Action buttons
        button_layout = QHBoxLayout()
        self.restore_button = QPushButton("Restore Selected")
        self.delete_button = QPushButton("Permanently Delete Selected")
        self.restore_button.clicked.connect(self.restore_selected)
        self.delete_button.clicked.connect(self.delete_selected)

        button_layout.addWidget(self.restore_button)
        button_layout.addWidget(self.delete_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def load_keep_images(self):
        """Load and display all images from keep"""
        self.keep_files = list(self.keep_folder.glob("*.*"))

        # Clear previous display
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        if not self.keep_files:
            no_results = QLabel("No images in keep")
            no_results.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_results, 0, 0, 1, 3)
            self.update_status()
            return

        # Display images
        for i, img_path in enumerate(self.keep_files):
            try:
                row, col = divmod(i, 3)
                image_frame = ClickableImageLabel(self)
                pixmap = QPixmap(str(img_path))
                if pixmap.isNull():
                    logging.error(f"Failed to load image: {img_path}")
                    continue
                image_frame.setPixmap(pixmap)
                image_frame.image_path = img_path
                self.grid_layout.addWidget(image_frame, row, col)
            except Exception as e:
                logging.error(f"Error displaying image {img_path}: {e}")

        self.update_status()

    def update_status(self):
        """Update status label"""
        count = len(self.keep_files)
        self.status_label.setText(f"Images in keep: {count}")

    def restore_selected(self):
        """Restore selected images to main folder"""
        restored_count = 0
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, ClickableImageLabel) and widget.selected:
                if restore_from_keep(widget.image_path, self.main_folder):
                    restored_count += 1

        if restored_count > 0:
            logging.info(f"Restored {restored_count} images from keep")
            self.close()

    def delete_selected(self):
        """Permanently delete selected images"""
        deleted_count = 0
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, ClickableImageLabel) and widget.selected:
                try:
                    os.remove(widget.image_path)
                    deleted_count += 1
                except Exception as e:
                    logging.error(f"Error deleting {widget.image_path}: {e}")

        if deleted_count > 0:
            logging.info(f"Permanently deleted {deleted_count} images")
            self.close()

    def close(self):
        """Emit finished signal and close the dialog"""
        self.finished.emit()
        super().close()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.restore_selected()
        elif event.key() == Qt.Key_Escape:
            self.close()
