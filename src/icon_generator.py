"""
Icon generator for PNG Folder Watch.
Creates crisp, modern icons for the system tray and GUI window.
"""

import os
from PIL import Image, ImageDraw, ImageFont

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(APP_DIR, "assets")
ICON_PNG_PATH = os.path.join(ASSETS_DIR, "icon.png")
ICON_ICO_PATH = os.path.join(ASSETS_DIR, "icon.ico")


def create_app_icon(size: int = 128) -> Image.Image:
    """Draw a modern, beautiful camera/photo conversion icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background rounded rectangle (vibrant indigo-cyan gradient look)
    margin = int(size * 0.08)
    radius = int(size * 0.22)
    
    # Rounded rect background
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=(37, 99, 235, 255),  # Modern Blue
        outline=(59, 130, 246, 255),
        width=int(size * 0.03),
    )

    # Inner photo card / fold
    card_x0 = int(size * 0.22)
    card_y0 = int(size * 0.25)
    card_x1 = int(size * 0.78)
    card_y1 = int(size * 0.75)
    card_rad = int(size * 0.08)

    draw.rounded_rectangle(
        [card_x0, card_y0, card_x1, card_y1],
        radius=card_rad,
        fill=(255, 255, 255, 245),
    )

    # Sun / Circle inside card
    sun_x = int(size * 0.35)
    sun_y = int(size * 0.38)
    sun_r = int(size * 0.07)
    draw.ellipse(
        [sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r],
        fill=(245, 158, 11, 255),  # Amber sun
    )

    # Mountain landscape inside card
    mountain1 = [
        (int(size * 0.26), int(size * 0.71)),
        (int(size * 0.45), int(size * 0.48)),
        (int(size * 0.62), int(size * 0.71)),
    ]
    draw.polygon(mountain1, fill=(16, 185, 129, 255))  # Emerald green

    mountain2 = [
        (int(size * 0.48), int(size * 0.71)),
        (int(size * 0.65), int(size * 0.54)),
        (int(size * 0.74), int(size * 0.71)),
    ]
    draw.polygon(mountain2, fill=(5, 150, 105, 255))  # Darker green

    # Conversion badge (arrow / badge in corner)
    badge_r = int(size * 0.18)
    bx = size - margin - int(badge_r * 0.7)
    by = size - margin - int(badge_r * 0.7)
    draw.ellipse(
        [bx - badge_r, by - badge_r, bx + badge_r, by + badge_r],
        fill=(249, 115, 22, 255),  # Orange badge
        outline=(255, 255, 255, 255),
        width=int(size * 0.03),
    )

    # Arrow inside badge (simple right arrow)
    ax0 = bx - int(badge_r * 0.45)
    ax1 = bx + int(badge_r * 0.45)
    ay = by
    arrow_w = max(2, int(size * 0.04))
    draw.line([(ax0, ay), (ax1, ay)], fill=(255, 255, 255, 255), width=arrow_w)
    draw.line([(ax1 - int(badge_r * 0.35), ay - int(badge_r * 0.35)), (ax1, ay)], fill=(255, 255, 255, 255), width=arrow_w)
    draw.line([(ax1 - int(badge_r * 0.35), ay + int(badge_r * 0.35)), (ax1, ay)], fill=(255, 255, 255, 255), width=arrow_w)

    return img


def ensure_icon_files():
    """Ensure icon.png and icon.ico exist on disk."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    if not os.path.exists(ICON_PNG_PATH) or not os.path.exists(ICON_ICO_PATH):
        img_large = create_app_icon(256)
        img_large.save(ICON_PNG_PATH, "PNG")
        
        # Save multi-size ICO
        sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img_large.save(ICON_ICO_PATH, format="ICO", sizes=sizes)
        print(f"[IconGenerator] Generated {ICON_PNG_PATH} and {ICON_ICO_PATH}")


if __name__ == "__main__":
    ensure_icon_files()
