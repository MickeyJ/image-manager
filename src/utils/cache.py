import json
from pathlib import Path
import logging
import hashlib
import shutil
from datetime import datetime


def get_folder_hash(folder_path, file_list):
    """Create a hash of the folder contents"""
    paths = sorted(str(p) for p in file_list)
    content = str(folder_path.resolve()) + "".join(paths)
    folder_hash = hashlib.md5(content.encode()).hexdigest()
    logging.info(f"Generated folder hash: {folder_hash[:8]}...")
    return folder_hash


def get_cache_dir(folder_path):
    """Returns path to cache directory"""
    cache_dir = Path(folder_path) / ".cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def get_cache_path(folder_path, cache_type):
    """Returns path to cache file"""
    cache_dir = get_cache_dir(folder_path)
    cache_path = cache_dir / f"{cache_type}_cache.json"
    logging.info(f"Cache path for {cache_type}: {cache_path}")
    return cache_path


def save_cache(folder_path, data, cache_type):
    """Save data to cache"""
    try:
        cache_path = get_cache_path(folder_path, cache_type)
        cache_data = {"timestamp": str(datetime.now()), "data": data}

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

        logging.info(f"Cache saved for {cache_type}")
        return True
    except Exception as e:
        logging.error(f"Failed to save {cache_type} cache: {e}")
        return False


def load_cache(folder_path, cache_type):
    """Load data from cache"""
    try:
        cache_path = get_cache_path(folder_path, cache_type)
        if not cache_path.exists():
            logging.info(f"No cache file found for {cache_type}")
            return None

        with open(cache_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        logging.info(f"Cache loaded for {cache_type} from {cache_data['timestamp']}")
        return cache_data["data"]
    except Exception as e:
        logging.error(f"Failed to load {cache_type} cache: {e}")
        return None


def clear_cache(folder_path, cache_type=None):
    """Clear cache files"""
    try:
        cache_dir = get_cache_dir(folder_path)
        if not cache_dir.exists():
            return

        if cache_type:
            # Clear specific cache
            cache_path = get_cache_path(folder_path, cache_type)
            if cache_path.exists():
                cache_path.unlink()
                logging.info(f"Cleared {cache_type} cache")

    except Exception as e:
        logging.error(f"Failed to clear cache: {e}")
