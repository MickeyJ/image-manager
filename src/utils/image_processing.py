import cv2
import numpy as np
import torch
from PIL import Image
import logging
from pathlib import Path
import traceback

try:
    import clip
except ImportError:
    clip = None

# Initialize CLIP model with error handling
try:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    if device == "cpu":
        logging.info("Running CLIP on CPU - this will be slower but still functional")
except Exception as e:
    logging.error(f"Error loading CLIP model: {e}")
    model = None
    preprocess = None


def get_image_embedding(image_path):
    try:
        if model is None or preprocess is None:
            logging.error("CLIP model not initialized")
            return None

        image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
        with torch.no_grad():
            embedding = model.encode_image(image)
            # Clear CUDA cache if using GPU
            if device == "cuda":
                torch.cuda.empty_cache()
        return embedding.cpu().numpy().flatten()
    except Exception as e:
        logging.error(f"Error processing image {image_path}: {e}")
        return None


def process_image_batch(image_paths, batch_size=32):
    """Process images in batches to prevent memory issues"""
    embeddings = []

    for i in range(0, len(image_paths), batch_size):
        batch = image_paths[i : i + batch_size]
        batch_embeddings = []

        for img_path in batch:
            emb = get_image_embedding(img_path)
            if emb is not None:
                batch_embeddings.append(emb)

        embeddings.extend(batch_embeddings)

        # Clear CUDA cache after each batch if using GPU
        if device == "cuda":
            torch.cuda.empty_cache()

    return embeddings


def are_images_similar(img1, img2, threshold=0.9):
    """Compare two images using perceptual hash"""
    try:

        # Try CLIP comparison
        if model is not None:
            emb1 = get_image_embedding(img1)
            emb2 = get_image_embedding(img2)
            if emb1 is not None and emb2 is not None:
                similarity = np.dot(emb1, emb2) / (
                    np.linalg.norm(emb1) * np.linalg.norm(emb2)
                )

                if similarity >= threshold:
                    logging.info(
                        f"CLIP MATCH: {Path(img1).name} and {Path(img2).name} (similarity: {similarity:.3f})"
                    )
                    return True
        else:
            logging.warning("CLIP model not available for comparison")

        return False
    except Exception as e:
        logging.error(f"Error comparing {Path(img1).name} with {Path(img2).name}: {e}")
        return False


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


def detect_noise(image_path, threshold=500):
    try:
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            logging.error(f"Failed to load image: {image_path}")
            return True

        noise = np.std(image)
        logging.debug(f"Noise level for {image_path}: {noise}")
        return noise > threshold
    except Exception as e:
        logging.error(f"Error checking noise for {image_path}: {e}")
        return True


def is_clip_available():
    """Check if CLIP model is properly initialized"""
    return model is not None and preprocess is not None


def get_clip_status():
    """Get detailed status of CLIP model"""
    if not is_clip_available():
        if model is None:
            return (
                "CLIP model failed to initialize. Please check your installation:\n"
                "1. Try reinstalling PyTorch and CLIP\n"
                "2. Check the logs for detailed error messages"
            )
    else:
        if device == "cuda":
            return "CLIP model ready (using GPU - best performance)"
        else:
            return "CLIP model ready (using CPU - slower but functional)"
