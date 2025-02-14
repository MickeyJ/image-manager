import json
from pathlib import Path
import logging
from datetime import datetime


def get_cache_path(image_folder, cache_type):
    """Returns path to cache file based on type (similar/blurry)"""
    # Create cache in project directory
    project_root = Path(__file__).parent.parent.parent
    cache_dir = project_root / ".cache"
    cache_dir.mkdir(exist_ok=True)

    # Use a hash of the image folder path to create unique cache files
    folder_hash = str(hash(str(image_folder)))
    return cache_dir / f"{cache_type}_{folder_hash}_cache.json"


def save_cache(cache_data, cache_path):
    """Save cache data to file"""
    with open(cache_path, "w") as f:
        json.dump(cache_data, f)
    logging.info(f"Cache saved to {cache_path}")


def load_cache(cache_path):
    """Load cache data from file"""
    try:
        with open(cache_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
