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

from ..utils.cache import load_cache, save_cache
from ..utils.image_processing import is_blurry, detect_noise
from ..utils.file_ops import get_recursive_image_files
from .widgets import ClickableImageLabel, LoadingSpinner


class BlurryImagesTab(QWidget):
    def __init__(self, image_folder, batch_size=1000):
        super().__init__()
        self.image_folder = Path(image_folder)
        self.batch_size = batch_size
        self.current_index = 0
        self.image_files = []
        self.bad_images = []
        self.scanning = False
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
        self.scan_button = QPushButton("Scan for Blurry/Noisy Images")
        self.scan_button.clicked.connect(self.find_bad_images)
        self.move_button = QPushButton("Move Selected to Limbo")
        self.move_button.clicked.connect(self.move_selected_to_limbo)

        action_layout.addWidget(self.scan_button)
        action_layout.addWidget(self.move_button)

        self.layout.addLayout(nav_layout)
        self.layout.addLayout(action_layout)
        self.setLayout(self.layout)
        self.update_button_states()

    def load_images(self):
        """Load image list from folder"""
        self.image_files = list(get_recursive_image_files(self.image_folder))
        self.update_status()

    def find_bad_images(self):
        if self.scanning:
            return

        self.scanning = True
        logging.info("Starting blurry image scan")

        # Try to load from cache
        cached_data = load_cache(self.image_folder, "blurry")
        if cached_data is not None:
            self.bad_images = [Path(p) for p in cached_data["bad_images"]]
            self.current_index = 0
            self.display_bad_images()
            self.scanning = False
            return

        spinner = LoadingSpinner(
            self,
            "Scanning for blurry and noisy images...",
            cancellable=True,
        )
        spinner.show()

        try:
            self.bad_images = []
            total_images = len(self.image_files)

            for i, img_path in enumerate(self.image_files):
                if spinner.was_cancelled:
                    self.status_label.setText("Scan cancelled")
                    break

                spinner.progress.setLabelText(f"Scanning image {i+1} of {total_images}")
                QApplication.processEvents()

                if is_blurry(str(img_path)) or detect_noise(str(img_path)):
                    self.bad_images.append(img_path)

            if not spinner.was_cancelled:
                # Save to cache
                cache_data = {"bad_images": [str(p) for p in self.bad_images]}
                save_cache(self.image_folder, cache_data, "blurry")

        finally:
            spinner.close()
            self.scanning = False
            self.display_bad_images()

    def display_bad_images(self):
        """Display the current batch of bad images"""
        # Clear previous display
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        if not self.bad_images:
            no_results = QLabel("No blurry or noisy images found")
            no_results.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_results, 0, 0, 1, 3)
            return

        # Display current batch
        batch_end = min(self.current_index + 9, len(self.bad_images))
        current_batch = self.bad_images[self.current_index : batch_end]

        for i, img_path in enumerate(current_batch):
            try:
                row, col = divmod(i, 3)
                image_frame = ClickableImageLabel(self, root_folder=self.image_folder)
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
        self.update_button_states()

    def update_status(self):
        """Update the status label with current position info"""
        if not self.bad_images:
            self.status_label.setText("No blurry or noisy images found")
            return

        batch_end = min(self.current_index + 9, len(self.bad_images))
        self.status_label.setText(
            f"Showing images {self.current_index + 1}-{batch_end} of {len(self.bad_images)}"
        )

    def update_button_states(self):
        """Update navigation button states"""
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index + 9 < len(self.bad_images))

    def prev_batch(self):
        """Show previous batch of images"""
        if self.current_index > 0:
            self.current_index = max(0, self.current_index - 9)
            self.display_bad_images()

    def next_batch(self):
        """Show next batch of images"""
        if self.current_index + 9 < len(self.bad_images):
            self.current_index += 9
            self.display_bad_images()

    def move_selected_to_limbo(self):
        """Move selected images to limbo folder"""
        limbo_folder = self.image_folder / "limbo"
        limbo_folder.mkdir(exist_ok=True)

        moved_count = 0
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, ClickableImageLabel) and widget.selected:
                if move_to_limbo(widget.image_path, limbo_folder):
                    moved_count += 1

        if moved_count > 0:
            # Refresh image lists
            self.image_files = list(get_recursive_image_files(self.image_folder))
            self.bad_images = [img for img in self.bad_images if img.exists()]
            self.display_bad_images()
