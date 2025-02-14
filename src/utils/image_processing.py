import cv2
import numpy as np
import imagehash
from PIL import Image
import logging
import torch
import clip

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
        logging.error(f"Error processing image {image_path}: {e}")
        return None


def is_blurry(image_path, threshold=100):
    try:
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            logging.error(f"Failed to load image: {image_path}")
            return True
        variance = cv2.Laplacian(image, cv2.CV_64F).var()
        return variance < threshold
    except Exception as e:
        logging.error(f"Error checking blur for {image_path}: {e}")
        return True


def are_images_similar(img1, img2, threshold=10):
    try:
        hash1 = imagehash.phash(Image.open(img1))
        hash2 = imagehash.phash(Image.open(img2))
        difference = abs(hash1 - hash2)
        return difference < threshold
    except Exception as e:
        logging.error(f"Error comparing images: {e}")
        return False


def detect_noise(image_path, threshold=500):
    """
    Detect if an image has excessive noise.

    Args:
        image_path: Path to the image file
        threshold: Noise threshold (higher means more tolerant of noise)

    Returns:
        bool: True if the image is noisy, False otherwise
    """
    try:
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            logging.error(f"Failed to load image: {image_path}")
            return True

        # Calculate image noise using standard deviation
        noise = np.std(image)
        logging.debug(f"Noise level for {image_path}: {noise}")
        return noise > threshold

    except Exception as e:
        logging.error(f"Error checking noise for {image_path}: {e}")
        return True
