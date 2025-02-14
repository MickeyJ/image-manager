from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import Qt
import logging

from .batch_tab import BatchViewTab
from .similar_tab import SimilarImagesTab
from .blurry_tab import BlurryImagesTab


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

        self.tabs.addTab(self.batch_tab, "Batch View")
        self.tabs.addTab(self.similar_tab, "Similar Images")
        self.tabs.addTab(self.blurry_tab, "Blurry/Noisy Images")

        layout.addWidget(self.tabs)

    def closeEvent(self, event):
        """Clean up resources before closing"""
        logging.info("Closing application")
        # Clean up CUDA memory if using GPU
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        event.accept()
