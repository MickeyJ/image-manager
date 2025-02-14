from pathlib import Path
import logging


def get_recursive_image_files(image_folder):
    """Get all image files recursively, excluding the limbo folder"""
    try:
        limbo_folder = Path(image_folder) / "limbo"
        image_files = [
            img
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]
            for img in Path(image_folder).rglob(ext)
            if limbo_folder not in img.parents
        ]
        logging.info(f"Found {len(image_files)} images in {image_folder}")
        return image_files
    except Exception as e:
        logging.error(f"Error getting image files: {e}")
        return []


def move_to_limbo(image_path, limbo_folder):
    """Move a file to the limbo folder, handling name conflicts"""
    try:
        source = Path(image_path)
        destination = limbo_folder / source.name
        counter = 1
        while destination.exists():
            destination = limbo_folder / f"{source.stem}_{counter}{source.suffix}"
            counter += 1
        source.rename(destination)
        logging.info(f"Moved {source} to limbo: {destination}")
        return True
    except Exception as e:
        logging.error(f"Error moving file to limbo: {e}")
        return False


def restore_from_limbo(source, main_folder):
    """Restore a file from limbo to main folder"""
    try:
        destination = main_folder / source.name
        counter = 1
        while destination.exists():
            destination = main_folder / f"{source.stem}_{counter}{source.suffix}"
            counter += 1
        source.rename(destination)
        logging.info(f"Restored {source} to {destination}")
        return True
    except Exception as e:
        logging.error(f"Error restoring file from limbo: {e}")
        return False
