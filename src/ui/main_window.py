from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import Qt
import logging
import torch

from .batch_tab import BatchViewTab
from .similar_tab import SimilarImagesTab
from .blurry_tab import BlurryImagesTab
from .trash_tab import TrashTab


class ImageManager(QMainWindow):
    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = image_folder
        self.initUI()

    def initUI(self):
        self.setWindowTitle("AI Image Manager")
        self.setMinimumSize(1000, 800)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create tab widget
        self.tabs = QTabWidget()

        # Create and add tabs
        self.batch_tab = BatchViewTab(self.image_folder)
        self.similar_tab = SimilarImagesTab(self.image_folder)
        self.blurry_tab = BlurryImagesTab(self.image_folder)
        self.trash_tab = TrashTab(self.image_folder)

        self.tabs.addTab(self.batch_tab, "Batch View")
        self.tabs.addTab(self.similar_tab, "Similar Images")
        self.tabs.addTab(self.blurry_tab, "Blurry/Noisy Images")
        self.tabs.addTab(self.trash_tab, "Trash")

        # Connect refresh signals
        self.batch_tab.refresh_view = self.refresh_all_tabs
        self.similar_tab.refresh_view = self.refresh_all_tabs
        self.blurry_tab.refresh_view = self.refresh_all_tabs
        self.trash_tab.refresh_view = self.refresh_all_tabs

        layout.addWidget(self.tabs)

    def refresh_all_tabs(self):
        """Refresh all tabs when files are moved"""
        self.batch_tab.load_images()
        self.trash_tab.load_images()
        # Only refresh other tabs if they're visible
        current_tab = self.tabs.currentWidget()
        if current_tab == self.similar_tab:
            self.similar_tab.load_images()
        elif current_tab == self.blurry_tab:
            self.blurry_tab.load_images()

    def closeEvent(self, event):
        """Clean up resources before closing"""
        logging.info("Closing application")
        # Clean up CUDA memory if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        event.accept()
