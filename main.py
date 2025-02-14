import sys
import os
import cv2
import torch
import clip
import numpy as np
import imagehash
from PIL import Image
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QFrame,
    QTabWidget,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from sklearn.cluster import KMeans
import argparse

# Load CLIP model
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)


def get_image_embedding(image_path):
    try:
        image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
        with torch.no_grad():
            embedding = model.encode_image(image)
        return embedding.cpu().numpy().flatten()
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None


def is_blurry(image_path, threshold=100):
    try:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            print(f"Failed to load image: {image_path}")
            return True
        variance = cv2.Laplacian(image, cv2.CV_64F).var()
        return variance < threshold
    except Exception as e:
        print(f"Error checking blur for {image_path}: {e}")
        return True


def detect_noise(image_path, threshold=500):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    noise = np.std(image)
    return noise > threshold


def are_images_similar(img1, img2, threshold=5):
    hash1 = imagehash.phash(Image.open(img1))
    hash2 = imagehash.phash(Image.open(img2))
    return abs(hash1 - hash2) < threshold


def should_delete(image_path):
    return is_blurry(image_path) or detect_noise(image_path)


def get_recursive_image_files(image_folder):
    # Create a Path object for the limbo folder
    limbo_folder = Path(image_folder) / "limbo"
    return [
        img
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]
        for img in Path(image_folder).rglob(ext)
        if limbo_folder not in img.parents  # Exclude limbo folder
    ]


class ImageLoader(QThread):
    image_loaded = pyqtSignal(int, QPixmap)

    def __init__(self, image_files, start_index):
        super().__init__()
        self.image_files = image_files
        self.start_index = start_index

    def run(self):
        for i in range(min(len(self.image_files) - self.start_index, 9)):
            pixmap = QPixmap(str(self.image_files[self.start_index + i]))
            self.image_loaded.emit(i, pixmap)


class ClickableImageLabel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.image_label = QLabel(self)
        self.layout.addWidget(self.image_label)

        # Center the image and make it fill the available space
        self.layout.setAlignment(Qt.AlignCenter)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(200, 200)  # Set minimum size

        # Style the frame
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
        # Scale the pixmap to fit the label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Rescale the pixmap when the label is resized
        if self.image_label.pixmap():
            self.image_label.setPixmap(
                self.image_label.pixmap().scaled(
                    self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )

    def mousePressEvent(self, event):
        self.selected = not self.selected
        self.setProperty("selected", self.selected)
        self.style().unpolish(self)
        self.style().polish(self)


class BatchViewTab(QWidget):
    def __init__(self, image_folder, batch_size=1000):
        super().__init__()
        self.image_folder = Path(image_folder)
        # Create limbo folder if it doesn't exist
        self.limbo_folder = self.image_folder / "limbo"
        self.limbo_folder.mkdir(exist_ok=True)

        self.batch_size = batch_size
        self.image_files = list(get_recursive_image_files(self.image_folder))[
            :batch_size
        ]
        self.current_index = 0
        self.selected_images = set()
        self.initUI()
        self.load_images()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.grid_layout = QGridLayout()

        # Create separate layouts for navigation and actions
        self.nav_layout = QHBoxLayout()
        self.action_layout = QHBoxLayout()

        # Navigation buttons with colors
        self.prev_button = QPushButton("Previous Batch", self)
        self.next_button = QPushButton("Next Batch", self)
        self.prev_button.clicked.connect(self.prev_batch)
        self.next_button.clicked.connect(self.next_batch)

        # Style the navigation buttons
        nav_button_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        self.prev_button.setStyleSheet(nav_button_style)
        self.next_button.setStyleSheet(nav_button_style)

        # Add navigation buttons
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.next_button)

        # Action buttons
        self.delete_button = QPushButton("Move to Limbo", self)
        self.restore_button = QPushButton("Restore from Limbo", self)
        self.delete_button.clicked.connect(self.delete_batch)
        self.restore_button.clicked.connect(self.restore_from_limbo)

        # Add action buttons
        self.action_layout.addWidget(self.delete_button)
        self.action_layout.addWidget(self.restore_button)

        # Add layouts to main layout
        self.layout.addLayout(self.grid_layout)
        self.layout.addLayout(self.nav_layout)
        self.layout.addLayout(self.action_layout)

        self.setLayout(self.layout)
        self.setWindowTitle("AI Image Reviewer - Grid View")
        self.resize(800, 600)

        # Update the grid layout properties
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)

        # Update button states
        self.update_button_states()

    def update_button_states(self):
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index + 9 < len(self.image_files))

    def prev_batch(self):
        if self.current_index > 0:
            self.current_index = max(0, self.current_index - 9)
            self.load_images()
        self.update_button_states()

    def next_batch(self):
        if self.current_index + 9 < len(self.image_files):
            self.current_index += 9
            self.load_images()
        self.update_button_states()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.next_batch()
        elif event.key() == Qt.Key_Left:
            self.prev_batch()
        elif event.key() == Qt.Key_Delete:
            self.delete_batch()

    def load_images(self):
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        self.loader = ImageLoader(self.image_files, self.current_index)
        self.loader.image_loaded.connect(self.place_image)
        self.loader.start()

    def place_image(self, i, pixmap):
        row, col = divmod(i, 3)
        image_frame = ClickableImageLabel(self)
        # Let the image fill the available space
        image_frame.setPixmap(pixmap)
        image_frame.image_index = self.current_index + i
        self.grid_layout.addWidget(image_frame, row, col)

    def delete_batch(self):
        # Get all visible image frames
        selected_to_move = []
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, ClickableImageLabel) and widget.selected:
                selected_to_move.append(widget.image_index)

        # If no images are selected, return
        if not selected_to_move:
            return

        # Move selected images to limbo
        for index in sorted(selected_to_move, reverse=True):
            source = self.image_files[index]
            destination = self.limbo_folder / source.name
            # Handle filename conflicts
            counter = 1
            while destination.exists():
                destination = (
                    self.limbo_folder / f"{source.stem}_{counter}{source.suffix}"
                )
                counter += 1
            source.rename(destination)

        # Refresh image list and display
        self.image_files = list(get_recursive_image_files(self.image_folder))[
            : self.batch_size
        ]
        self.load_images()

    def restore_from_limbo(self):
        # Create a new dialog to show limbo images
        self.limbo_dialog = LimboDialog(self.limbo_folder, self.image_folder)
        self.limbo_dialog.finished.connect(
            self.refresh_images
        )  # Connect directly to refresh_images
        self.limbo_dialog.show()

    def refresh_images(self):
        self.image_files = list(get_recursive_image_files(self.image_folder))[
            : self.batch_size
        ]
        self.load_images()


class SimilarImagesTab(QWidget):
    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = Path(image_folder)
        self.image_files = list(get_recursive_image_files(self.image_folder))
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.button_layout = QHBoxLayout()

        self.scan_button = QPushButton("Scan for Similar Images", self)
        self.scan_button.clicked.connect(self.find_similar_images)
        self.button_layout.addWidget(self.scan_button)

        self.layout.addLayout(self.grid_layout)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def find_similar_images(self):
        similar_groups = []
        processed = set()

        for i, img1 in enumerate(self.image_files):
            if str(img1) in processed:
                continue

            current_group = [img1]
            for img2 in self.image_files[i + 1 :]:
                if str(img2) in processed:
                    continue
                if are_images_similar(str(img1), str(img2)):
                    current_group.append(img2)
                    processed.add(str(img2))

            if len(current_group) > 1:
                similar_groups.append(current_group)
                processed.add(str(img1))

        self.display_similar_groups(similar_groups)

    def display_similar_groups(self, groups):
        # Clear previous display
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        current_row = 0
        for group in groups:
            # Add a separator label
            separator = QLabel(f"Similar Group ({len(group)} images)")
            self.grid_layout.addWidget(separator, current_row, 0, 1, 3)
            current_row += 1

            # Display images in the group
            for i, img_path in enumerate(group):
                col = i % 3
                if col == 0 and i != 0:
                    current_row += 1

                image_frame = ClickableImageLabel(self)
                pixmap = QPixmap(str(img_path))
                image_frame.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
                self.grid_layout.addWidget(image_frame, current_row, col)

            current_row += 2  # Add space between groups


class BlurryImagesTab(QWidget):
    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = Path(image_folder)
        self.image_files = list(get_recursive_image_files(self.image_folder))
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.button_layout = QHBoxLayout()

        self.scan_button = QPushButton("Scan for Blurry/Noisy Images", self)
        self.scan_button.clicked.connect(self.find_bad_images)
        self.button_layout.addWidget(self.scan_button)

        self.layout.addLayout(self.grid_layout)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

    def find_bad_images(self):
        bad_images = []
        for img_path in self.image_files:
            if should_delete(str(img_path)):
                bad_images.append(img_path)

        self.display_bad_images(bad_images)

    def display_bad_images(self, images):
        # Clear previous display
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        for i, img_path in enumerate(images):
            row, col = divmod(i, 3)
            image_frame = ClickableImageLabel(self)
            pixmap = QPixmap(str(img_path))
            image_frame.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            self.grid_layout.addWidget(image_frame, row, col)


class ImageReviewer(QWidget):
    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = Path(image_folder)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Create tabs
        self.batch_tab = BatchViewTab(self.image_folder)
        self.similar_tab = SimilarImagesTab(self.image_folder)
        self.blurry_tab = BlurryImagesTab(self.image_folder)

        # Add tabs
        self.tabs.addTab(self.batch_tab, "Batch View")
        self.tabs.addTab(self.similar_tab, "Similar Images")
        self.tabs.addTab(self.blurry_tab, "Blurry/Noisy Images")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.setWindowTitle("AI Image Reviewer")
        self.resize(800, 600)

    def closeEvent(self, event):
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        event.accept()


def cluster_images(image_folder, num_clusters=5):
    image_files = get_recursive_image_files(image_folder)
    embeddings = np.array([get_image_embedding(str(img)) for img in image_files])
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    clusters = kmeans.fit_predict(embeddings)
    for idx, img_path in enumerate(image_files):
        cluster_folder = Path(image_folder) / f"Cluster_{clusters[idx]}"
        cluster_folder.mkdir(exist_ok=True)
        os.rename(img_path, cluster_folder / img_path.name)


# Add a signal class for the limbo dialog
class LimboDialogSignals(QObject):
    finished = pyqtSignal()


class LimboDialog(QWidget):
    def __init__(self, limbo_folder, main_folder):
        super().__init__()
        self.limbo_folder = limbo_folder
        self.main_folder = main_folder
        # Add signals
        self.signals = LimboDialogSignals()
        self.finished = self.signals.finished  # Make the finished signal accessible
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Restore from Limbo")
        self.layout = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.button_layout = QHBoxLayout()

        # Add buttons
        self.restore_button = QPushButton("Restore Selected", self)
        self.restore_button.clicked.connect(self.restore_selected)
        self.delete_button = QPushButton("Permanently Delete Selected", self)
        self.delete_button.clicked.connect(self.delete_selected)

        self.button_layout.addWidget(self.restore_button)
        self.button_layout.addWidget(self.delete_button)

        self.layout.addLayout(self.grid_layout)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

        # Load limbo images
        self.load_limbo_images()

        self.resize(800, 600)

    def load_limbo_images(self):
        self.limbo_files = list(self.limbo_folder.glob("*.*"))

        for i, img_path in enumerate(self.limbo_files):
            row, col = divmod(i, 3)
            image_frame = ClickableImageLabel(self)
            pixmap = QPixmap(str(img_path))
            image_frame.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
            image_frame.image_path = img_path
            self.grid_layout.addWidget(image_frame, row, col)

    def restore_selected(self):
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, ClickableImageLabel) and widget.selected:
                source = widget.image_path
                destination = self.main_folder / source.name
                # Handle filename conflicts
                counter = 1
                while destination.exists():
                    destination = (
                        self.main_folder / f"{source.stem}_{counter}{source.suffix}"
                    )
                    counter += 1
                source.rename(destination)
        self.close()

    def delete_selected(self):
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if isinstance(widget, ClickableImageLabel) and widget.selected:
                os.remove(widget.image_path)
        self.close()

    def close(self):
        self.finished.emit()  # Emit the finished signal before closing
        super().close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Management Tool")
    parser.add_argument(
        "--folder", type=str, required=True, help="Path to image folder"
    )
    parser.add_argument(
        "--cluster", action="store_true", help="Perform clustering before viewing"
    )
    args = parser.parse_args()

    if args.cluster:
        cluster_images(args.folder)

    app = QApplication(sys.argv)
    window = ImageReviewer(args.folder)
    window.show()
    sys.exit(app.exec_())
