#!/usr/bin/env python3
import sys
from pathlib import Path
from main import main

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: launch.py <image_folder>")
        sys.exit(1)

    folder = Path(sys.argv[1])
    if not folder.exists():
        print(f"Folder not found: {folder}")
        sys.exit(1)

    sys.argv = [sys.argv[0], "--folder", str(folder)]
    main()
