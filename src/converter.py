"""
PNG to JPG Conversion Module.
Handles image loading, alpha channel detection, path computation,
JPEG conversion with quality settings, and original file retention/deletion.
"""

import os
import time
from typing import Tuple, Dict, Any, Optional
from PIL import Image

from .config import (
    OUTPUT_MODE_SAME,
    OUTPUT_MODE_JPG_SUB,
    OUTPUT_MODE_MIRROR,
    KEEP_ORIGINAL_ALWAYS,
    KEEP_ORIGINAL_NEVER,
    KEEP_ORIGINAL_DELETE_NO_ALPHA,
)


# Minimum alpha value considered meaningfully transparent (values >= 254 are treated as opaque,
# filtering out 254 quantization noise common in Unity / VRChat rendering).
ALPHA_OPAQUE_THRESHOLD = 254


def has_alpha_channel(img: Image.Image, alpha_threshold: int = ALPHA_OPAQUE_THRESHOLD) -> bool:
    """
    Check if the image contains meaningful transparency / alpha channel information.
    Returns True if transparent or semi-transparent pixels exist.
    Alpha values >= alpha_threshold (default 254) are treated as opaque.
    """
    try:
        # Check standard RGBA / LA / PA modes
        if img.mode in ("RGBA", "LA", "PA"):
            alpha = img.getchannel("A")
            min_val, max_val = alpha.getextrema()
            # If minimum alpha is < alpha_threshold, at least one pixel is transparent/translucent
            return min_val < alpha_threshold

        # Palette mode with transparency info
        if img.mode == "P" and "transparency" in img.info:
            transparency = img.info["transparency"]
            if isinstance(transparency, bytes):
                # Alpha palette
                return min(transparency) < alpha_threshold
            elif isinstance(transparency, int):
                # Single transparent index used
                # Check if this index actually appears in the image
                colors = img.getcolors(maxcolors=256)
                if colors:
                    for count, idx in colors:
                        if idx == transparency:
                            return True
            return True

        return False
    except Exception as e:
        print(f"[Converter] Error checking alpha channel: {e}")
        return False


def compute_target_path(png_path: str, watch_folder: str, output_mode: str) -> str:
    """
    Compute the destination JPG file path based on the rule's output mode.
    """
    png_path = os.path.abspath(png_path)
    watch_folder = os.path.abspath(watch_folder)
    png_dir = os.path.dirname(png_path)
    stem, _ = os.path.splitext(os.path.basename(png_path))
    jpg_filename = f"{stem}.jpg"

    if output_mode == OUTPUT_MODE_JPG_SUB:
        # Save in ./jpg/* relative to current PNG's directory
        target_dir = os.path.join(png_dir, "jpg")
        return os.path.join(target_dir, jpg_filename)

    elif output_mode == OUTPUT_MODE_MIRROR:
        # Mimic structure in <root>/../jpg-<root_name>/<relative_path>
        root_parent = os.path.dirname(watch_folder)
        root_name = os.path.basename(watch_folder)
        if not root_name:
            root_name = "root"
        mirror_root = os.path.join(root_parent, f"jpg-{root_name}")

        try:
            rel_dir = os.path.relpath(png_dir, watch_folder)
        except ValueError:
            # Different drive or invalid relative path
            rel_dir = ""

        if rel_dir and rel_dir != ".":
            target_dir = os.path.join(mirror_root, rel_dir)
        else:
            target_dir = mirror_root
        return os.path.join(target_dir, jpg_filename)

    else:
        # Default: OUTPUT_MODE_SAME
        return os.path.join(png_dir, jpg_filename)


def wait_for_file_ready(filepath: str, timeout: float = 6.0, poll_interval: float = 0.3) -> bool:
    """
    Wait until a newly created file has finished writing and is unlocked.
    Checks file size stability and ability to open.
    """
    start_time = time.time()
    last_size = -1
    stable_count = 0

    while time.time() - start_time < timeout:
        if not os.path.exists(filepath):
            time.sleep(poll_interval)
            continue

        try:
            current_size = os.path.getsize(filepath)
            if current_size > 0 and current_size == last_size:
                stable_count += 1
                if stable_count >= 2:
                    # Verify read access
                    with open(filepath, "rb") as f:
                        f.read(128)
                    return True
            else:
                stable_count = 0
                last_size = current_size
        except (PermissionError, OSError):
            stable_count = 0

        time.sleep(poll_interval)

    # Final attempt
    try:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            with open(filepath, "rb") as f:
                f.read(128)
            return True
    except Exception:
        pass
    return False


def convert_png_to_jpg(
    png_path: str,
    rule: Dict[str, Any],
    on_complete_callback: Optional[callable] = None,
) -> Tuple[bool, str, Optional[str], bool]:
    """
    Convert a single PNG file to JPG according to rule settings.
    
    Returns:
        (success: bool, message: str, target_path: Optional[str], deleted_original: bool)
    """
    if not os.path.exists(png_path):
        return False, f"File not found: {png_path}", None, False

    if not png_path.lower().endswith(".png"):
        return False, "Not a PNG file", None, False

    # Wait for file to finish writing
    if not wait_for_file_ready(png_path):
        return False, f"File busy or not ready: {png_path}", None, False

    watch_folder = rule.get("watch_folder", "")
    output_mode = rule.get("output_mode", OUTPUT_MODE_SAME)
    keep_original = rule.get("keep_original", KEEP_ORIGINAL_ALWAYS)
    jpg_quality = int(rule.get("jpg_quality", 90))
    jpg_quality = max(1, min(100, jpg_quality))

    target_path = compute_target_path(png_path, watch_folder, output_mode)

    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        with Image.open(png_path) as img:
            has_alpha = has_alpha_channel(img)

            # Convert to RGB (JPEG requirement)
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                rgba_img = img.convert("RGBA")
                # White background for transparent areas
                bg = Image.new("RGB", rgba_img.size, (255, 255, 255))
                bg.paste(rgba_img, mask=rgba_img.split()[3])
                rgb_img = bg
            else:
                rgb_img = img.convert("RGB")

            # Save as JPEG
            rgb_img.save(target_path, "JPEG", quality=jpg_quality, optimize=True)

        deleted_original = False

        # Handle keep/delete original
        if keep_original == KEEP_ORIGINAL_NEVER:
            try:
                os.remove(png_path)
                deleted_original = True
            except Exception as e:
                print(f"[Converter] Could not delete original {png_path}: {e}")

        elif keep_original == KEEP_ORIGINAL_DELETE_NO_ALPHA:
            if not has_alpha:
                try:
                    os.remove(png_path)
                    deleted_original = True
                except Exception as e:
                    print(f"[Converter] Could not delete original {png_path}: {e}")
            else:
                # Kept because it has transparency
                deleted_original = False

        msg = f"Converted '{os.path.basename(png_path)}' -> '{os.path.basename(target_path)}'"
        if deleted_original:
            msg += " (original removed)"
        elif keep_original == KEEP_ORIGINAL_DELETE_NO_ALPHA and has_alpha:
            msg += " (original kept: contains transparency)"

        if on_complete_callback:
            try:
                on_complete_callback(png_path, target_path, deleted_original)
            except Exception:
                pass

        return True, msg, target_path, deleted_original

    except Exception as e:
        err_msg = f"Error converting {png_path}: {e}"
        print(f"[Converter] {err_msg}")
        return False, err_msg, None, False
