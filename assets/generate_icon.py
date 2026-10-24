"""Regenerate CorePulse PNG and multi-resolution Windows ICO branding assets.

This helper is intentionally a development-only script.  The generated binaries are
checked into the project, so Pillow is not required to run CorePulse.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
SIZE = 1024


def create_icon() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), "#08090B")
    # A faint orange glow beneath the emblem, kept subtle for taskbar sizes.
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((160, 160, 864, 864), fill=(255, 129, 38, 42))
    glow = glow.filter(ImageFilter.GaussianBlur(105))
    image.alpha_composite(glow)

    draw = ImageDraw.Draw(image)
    draw.ellipse((104, 104, 920, 920), fill="#0D0F12", outline="#303640", width=18)
    draw.ellipse((156, 156, 868, 868), outline="#1E232A", width=18)

    # Broken orange performance ring: a recognizable silhouette even at 16 px.
    draw.arc((210, 210, 814, 814), 34, 317, fill="#FF8126", width=76)
    draw.arc((228, 228, 796, 796), 34, 317, fill="#FFB16E", width=18)

    # White-orange ECG/pulse stroke.
    points = [
        (245, 520), (360, 520), (420, 520), (476, 385), (548, 654),
        (625, 462), (678, 520), (779, 520),
    ]
    draw.line(points, fill="#FFF5EF", width=39, joint="curve")
    # Rounded endpoints / vertices soften the geometry.
    for x, y in points:
        draw.ellipse((x - 19, y - 19, x + 19, y + 19), fill="#FFF5EF")
    draw.ellipse((245 - 18, 520 - 18, 245 + 18, 520 + 18), fill="#FFB16E")
    draw.ellipse((779 - 18, 520 - 18, 779 + 18, 520 + 18), fill="#FFB16E")
    return image


def main() -> None:
    icon = create_icon()
    png = ROOT / "corepulse.png"
    ico = ROOT / "corepulse.ico"
    icon.save(png, "PNG", optimize=True)
    icon.save(
        ico,
        "ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Wrote {png.name} and {ico.name}")


if __name__ == "__main__":
    main()
