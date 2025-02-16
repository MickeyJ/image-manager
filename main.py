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
    QProgressDialog,
    QScrollArea,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from sklearn.cluster import KMeans
import argparse
import logging
import json
from datetime import datetime

from src.ui.main_window import ImageManager


def setup_logging():
    """Set up logging configuration"""
    log_file = "image_manager.log"

    # Clear previous log file
    with open(log_file, "w") as f:
        f.write("")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),  # Also print to console
        ],
    )
    logging.info("Logging initialized")


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="AI Image Management Tool")
    parser.add_argument(
        "--folder", type=str, required=True, help="Path to image folder"
    )
    args = parser.parse_args()

    logging.info("App Starting")

    # Check if CUDA is available
    logging.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logging.info(f"CUDA device: {torch.cuda.get_device_name(0)}")

    # Validate folder
    image_folder = Path(args.folder)
    if not image_folder.exists():
        logging.error(f"Folder not found: {image_folder}")
        return 1

    # Create application
    app = QApplication(sys.argv)
    window = ImageManager(image_folder)
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
