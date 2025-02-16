from pathlib import Path
import logging


def get_recursive_image_files(image_folder):
    """Get all image files recursively, excluding the keep folder"""
    try:
        keep_folder = Path(image_folder) / "keep"
        image_files = [
            img
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]
            for img in Path(image_folder).rglob(ext)
            if keep_folder not in img.parents
        ]
        logging.info(f"Found {len(image_files)} images in {image_folder}")
        return image_files
    except Exception as e:
        logging.error(f"Error getting image files: {e}")
        return []


def move_to_keep(image_path, keep_folder):
    """Move a file to the keep folder, handling name conflicts"""
    try:
        source = Path(image_path)
        destination = keep_folder / source.name
        counter = 1
        while destination.exists():
            destination = keep_folder / f"{source.stem}_{counter}{source.suffix}"
            counter += 1
        source.rename(destination)
        logging.info(f"Moved {source} to keep: {destination}")
        return True
    except Exception as e:
        logging.error(f"Error moving file to keep: {e}")
        return False


def restore_from_keep(source, main_folder):
    """Restore a file from keep to main folder"""
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
        logging.error(f"Error restoring file from keep: {e}")
        return False


def move_to_trash(image_path, root_folder=None):
    """Move a file to the trash folder"""
    try:
        source = Path(image_path)
        if not source.exists():
            logging.error(f"Source file does not exist: {source}")
            return False

        # Use the root folder to create trash in correct location
        if root_folder is None:
            root_folder = source.parent.parent  # Fallback, but shouldn't be used
            logging.warning("No root folder provided for trash - using parent.parent")

        trash_folder = Path(root_folder) / "trash"
        trash_folder.mkdir(exist_ok=True)

        destination = trash_folder / source.name
        counter = 1
        while destination.exists():
            stem = source.stem
            suffix = source.suffix
            destination = trash_folder / f"{stem}_{counter}{suffix}"
            counter += 1

        source.rename(destination)
        if destination.exists() and not source.exists():
            logging.info(f"Moved {source.name} to trash ({destination})")
            return True
        else:
            logging.error(f"Failed to move {source.name} to trash")
            return False

    except Exception as e:
        logging.error(f"Error moving file to trash: {e}")
        return False


def restore_from_trash(image_path):
    """Restore a file from trash to original folder"""
    try:
        source = Path(image_path)
        main_folder = source.parent.parent

        # Create unique name if file exists
        destination = main_folder / source.name
        counter = 1
        while destination.exists():
            stem = source.stem
            suffix = source.suffix
            destination = main_folder / f"{stem}_{counter}{suffix}"
            counter += 1

        # Actually move the file
        source.rename(destination)
        logging.info(f"Restored {source.name} from trash to ({destination})")
        return True
    except Exception as e:
        logging.error(f"Error restoring file from trash: {e}")
        return False


def delete_trash(folder_path):
    """Permanently delete all files in trash folder"""
    try:
        trash_folder = Path(folder_path) / "trash"
        if not trash_folder.exists():
            return True

        for file in trash_folder.iterdir():
            if file.is_file():
                file.unlink()
                logging.info(f"Deleted {file}")

        return True
    except Exception as e:
        logging.error(f"Error deleting trash: {e}")
        return False
