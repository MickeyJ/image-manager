from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGridLayout,
    QScrollArea,
    QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from pathlib import Path
import logging

from ..utils.file_ops import get_recursive_image_files, move_to_limbo
from .widgets import ClickableImageLabel, LoadingSpinner


class BatchViewTab(QWidget):
    def __init__(self, image_folder, batch_size=1000):
        super().__init__()
        self.image_folder = Path(image_folder)
        self.batch_size = batch_size
        self.current_index = 0

        # Create limbo folder if it doesn't exist
        self.limbo_folder = self.image_folder / "limbo"
        self.limbo_folder.mkdir(exist_ok=True)

        self.image_files = []
        self.initUI()
        self.load_images()

    def initUI(self):
        self.layout = QVBoxLayout()

        # Status label at top
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

        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous Batch")
        self.next_button = QPushButton("Next Batch")
        self.prev_button.clicked.connect(self.prev_batch)
        self.next_button.clicked.connect(self.next_batch)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)

        # Action buttons
        action_layout = QHBoxLayout()
        self.move_button = QPushButton("Move Selected to Limbo")
        self.restore_button = QPushButton("Restore from Limbo")
        self.move_button.clicked.connect(self.move_selected_to_limbo)
        self.restore_button.clicked.connect(self.restore_from_limbo)

        action_layout.addWidget(self.move_button)
        action_layout.addWidget(self.restore_button)

        self.layout.addLayout(nav_layout)
        self.layout.addLayout(action_layout)
        self.setLayout(self.layout)

    def load_images(self):
        """Load image list and display current batch"""
        self.image_files = list(get_recursive_image_files(self.image_folder))
        self.display_current_batch()
        self.update_status()

    def display_current_batch(self):
        """Display the current batch of images"""
        # Clear previous display
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        if not self.image_files:
            no_results = QLabel("No images found")
            no_results.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_results, 0, 0, 1, 3)
            return

        # Display current batch
        batch_end = min(self.current_index + 9, len(self.image_files))
        current_batch = self.image_files[self.current_index : batch_end]

        for i, img_path in enumerate(current_batch):
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

        self.update_button_states()

    def update_status(self):
        """Update the status label with current position info"""
        if not self.image_files:
            self.status_label.setText("No images found")
            return

        batch_end = min(self.current_index + 9, len(self.image_files))
        self.status_label.setText(
            f"Showing images {self.current_index + 1}-{batch_end} of {len(self.image_files)}"
        )

    def update_button_states(self):
        """Update navigation button states"""
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index + 9 < len(self.image_files))

    def prev_batch(self):
        """Show previous batch of images"""
        if self.current_index > 0:
            self.current_index = max(0, self.current_index - 9)
            self.display_current_batch()
            self.update_status()

    def next_batch(self):
        """Show next batch of images"""
        if self.current_index + 9 < len(self.image_files):
            self.current_index += 9
            self.display_current_batch()
            self.update_status()

    def move_selected_to_limbo(self):
        """Move selected images to limbo folder"""
        moved_count = 0
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, ClickableImageLabel) and widget.selected:
                if move_to_limbo(widget.image_path, self.limbo_folder):
                    moved_count += 1

        if moved_count > 0:
            self.load_images()  # Refresh the view

    def restore_from_limbo(self):
        """Open the limbo dialog"""
        from .limbo_dialog import LimboDialog

        self.limbo_dialog = LimboDialog(self.limbo_folder, self.image_folder)
        self.limbo_dialog.finished.connect(self.load_images)
        self.limbo_dialog.show()

    def keyPressEvent(self, event):
        """Handle keyboard navigation"""
        if event.key() == Qt.Key_Right:
            self.next_batch()
        elif event.key() == Qt.Key_Left:
            self.prev_batch()
        elif event.key() == Qt.Key_Delete:
            self.move_selected_to_limbo()
