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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="AI Image Management Tool")
    parser.add_argument(
        "--folder", type=str, required=True, help="Path to image folder"
    )
    args = parser.parse_args()

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
