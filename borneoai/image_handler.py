import os
import mimetypes

def find_images(filter_text="", workspace_root="."):
    """
    Scans common image directories and the workspace root for images.
    Returns a list of absolute paths to images.
    """
    # Common image extensions
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
    
    # Directories to scan
    scan_dirs = [workspace_root]
    
    # Common Android paths and root search
    possible_android_paths = [
        "/sdcard",
        "/sdcard/DCIM/Camera",
        "/sdcard/Pictures",
        "/storage/emulated/0",
        "/storage/emulated/0/DCIM/Camera",
        "/storage/emulated/0/Pictures"
    ]
    
    for path in possible_android_paths:
        if os.path.exists(path):
            scan_dirs.append(path)

    found_images = []
    
    for scan_dir in scan_dirs:
        try:
            # Use os.walk but limit depth or handle errors to avoid hanging on system dirs
            for root, _, files in os.walk(scan_dir):
                # Safety: avoid scanning too many directories if we are at root
                if root == "/":
                    # Only scan top level if at root to avoid infinite loop/slowness
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in IMAGE_EXTENSIONS:
                            if not filter_text or filter_text.lower() in file.lower():
                                found_images.append(os.path.join(root, file))
                    break
                
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in IMAGE_EXTENSIONS:
                        if not filter_text or filter_text.lower() in file.lower():
                            found_images.append(os.path.join(root, file))
        except Exception:
            continue # Skip directories we can't access

    # Remove duplicates
    return list(set(found_images))

def get_image_name(path):
    return os.path.basename(path)
