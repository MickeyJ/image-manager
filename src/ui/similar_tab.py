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

from ..utils.cache import get_cache_path, save_cache, load_cache
from ..utils.image_processing import are_images_similar
from ..utils.file_ops import get_recursive_image_files, move_to_limbo
from .widgets import ClickableImageLabel, LoadingSpinner


class SimilarImagesTab(QWidget):
    def __init__(self, image_folder, batch_size=1000):
        super().__init__()
        self.image_folder = Path(image_folder)
        self.batch_size = batch_size
        self.current_index = 0
        self.image_files = []
        self.similar_groups = []
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
        self.prev_button = QPushButton("Previous Groups")
        self.next_button = QPushButton("Next Groups")
        self.prev_button.clicked.connect(self.prev_batch)
        self.next_button.clicked.connect(self.next_batch)
        self.prev_button.setToolTip("Show previous groups (Left Arrow)")
        self.next_button.setToolTip("Show next groups (Right Arrow)")
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)

        # Action buttons
        action_layout = QHBoxLayout()
        self.scan_button = QPushButton("Scan for Similar Images")
        self.scan_button.clicked.connect(self.find_similar_images)
        self.scan_button.setToolTip(
            "Find groups of similar images (may take several minutes)"
        )

        self.move_button = QPushButton("Move Selected to Limbo")
        self.move_button.clicked.connect(self.move_selected_to_limbo)
        self.move_button.setToolTip("Move selected images to limbo (Delete)")

        action_layout.addWidget(self.scan_button)
        action_layout.addWidget(self.move_button)

        self.layout.addLayout(nav_layout)
        self.layout.addLayout(action_layout)
        self.setLayout(self.layout)

    def load_images(self):
        """Load image list from folder"""
        self.image_files = list(get_recursive_image_files(self.image_folder))
        self.update_status()

    def find_similar_images(self):
        if self.scanning:
            return

        self.scanning = True
        cache_path = get_cache_path(self.image_folder, "similar")
        cache_data = load_cache(cache_path)

        # Check cache
        if cache_data and "groups" in cache_data:  # Add check for "groups" key
            current_files = set(str(f) for f in self.image_files)
            try:
                cached_files = set(
                    path for group in cache_data["groups"] for path in group
                )

                if current_files == cached_files:
                    logging.info("Using cached similar images data")
                    self.similar_groups = [
                        [Path(p) for p in group] for group in cache_data["groups"]
                    ]
                    self.current_index = 0
                    self.display_similar_groups()
                    self.scanning = False
                    return
                else:
                    logging.info("Cache invalid - file list changed")
            except Exception as e:
                logging.error(f"Error loading cache: {e}")

        # Start new scan
        total_images = len(self.image_files)
        if total_images > 1000:
            self.status_label.setText(
                f"Scanning {total_images} images. This may take a while..."
            )

        spinner = LoadingSpinner(
            self,
            f"Scanning {total_images} images for similarities...",
            cancellable=True,
        )
        spinner.show()

        self.similar_groups = []
        processed = set()

        try:
            for i, img1 in enumerate(self.image_files):
                if spinner.was_cancelled:
                    self.status_label.setText("Scan cancelled")
                    break

                if str(img1) in processed:
                    continue

                current_group = [img1]
                spinner.progress.setLabelText(f"Scanning image {i+1} of {total_images}")
                QApplication.processEvents()

                for img2 in self.image_files[i + 1 :]:
                    if spinner.was_cancelled:
                        break

                    if str(img2) in processed:
                        continue

                    if are_images_similar(str(img1), str(img2)):
                        current_group.append(img2)
                        processed.add(str(img2))

                if len(current_group) > 1:
                    self.similar_groups.append(current_group)
                    processed.add(str(img1))

            if not spinner.was_cancelled:
                # Sort groups by size
                self.similar_groups.sort(key=len, reverse=True)
                # Save cache
                cache_data = {
                    "groups": [[str(p) for p in group] for group in self.similar_groups]
                }
                save_cache(cache_data, cache_path)

        finally:
            spinner.close()
            self.scanning = False
            self.display_similar_groups()

    def display_similar_groups(self):
        """Display the current batch of similar image groups"""
        # Clear previous display
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        if not self.similar_groups:
            no_results = QLabel("No similar images found")
            no_results.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_results, 0, 0, 1, 3)
            return

        # Display current batch
        batch_end = min(self.current_index + 3, len(self.similar_groups))
        current_groups = self.similar_groups[self.current_index : batch_end]

        current_row = 0
        for group_idx, group in enumerate(current_groups):
            # Add group header
            separator = QLabel(
                f"Similar Group {self.current_index + group_idx + 1} ({len(group)} images)"
            )
            separator.setStyleSheet("font-weight: bold; padding: 10px;")
            self.grid_layout.addWidget(separator, current_row, 0, 1, 3)
            current_row += 1

            # Add images in the group
            for i, img_path in enumerate(group):
                try:
                    col = i % 3
                    if col == 0 and i != 0:
                        current_row += 1

                    image_frame = ClickableImageLabel(self)
                    pixmap = QPixmap(str(img_path))
                    if pixmap.isNull():
                        logging.error(f"Failed to load image: {img_path}")
                        continue
                    image_frame.setPixmap(pixmap)
                    image_frame.image_path = img_path
                    self.grid_layout.addWidget(image_frame, current_row, col)
                except Exception as e:
                    logging.error(f"Error displaying image {img_path}: {e}")

            current_row += 2  # Add space between groups

        self.update_status()
        self.update_button_states()

    def update_status(self):
        """Update the status label with current position info"""
        if not self.similar_groups:
            self.status_label.setText("No similar images found")
            return

        batch_end = min(self.current_index + 3, len(self.similar_groups))
        total_images = sum(len(group) for group in self.similar_groups)
        self.status_label.setText(
            f"Showing groups {self.current_index + 1}-{batch_end} of {len(self.similar_groups)} "
            f"(Total similar images: {total_images})"
        )

    def update_button_states(self):
        """Update navigation button states"""
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index + 3 < len(self.similar_groups))

    def prev_batch(self):
        """Show previous batch of groups"""
        if self.current_index > 0:
            self.current_index = max(0, self.current_index - 3)
            self.display_similar_groups()

    def next_batch(self):
        """Show next batch of groups"""
        if self.current_index + 3 < len(self.similar_groups):
            self.current_index += 3
            self.display_similar_groups()

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
            # Refresh image lists and remove moved images from groups
            self.image_files = list(get_recursive_image_files(self.image_folder))
            # Update groups to remove moved images
            self.similar_groups = [
                [img for img in group if img.exists()] for group in self.similar_groups
            ]
            # Remove empty groups
            self.similar_groups = [
                group for group in self.similar_groups if len(group) > 1
            ]
            self.display_similar_groups()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Right:
            self.next_batch()
        elif event.key() == Qt.Key_Left:
            self.prev_batch()
        elif event.key() == Qt.Key_Delete:
            self.move_selected_to_limbo()
