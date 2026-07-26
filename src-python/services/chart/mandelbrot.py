"""
Simple Mandelbrot-like fractal image generator.

Purpose
- Quickly generate small, visually pleasing, and variable "fractal snapshot" images
  that can be attached to Telegram messages as charts.
- The image is intentionally parameterized so it can act as a creative snapshot of
  a few parameters (center, scale, iterations, palette seed).

Notes / dependencies
- Requires: numpy and pillow (PIL)
  Install with: pip install numpy pillow

API
- generate_mandelbrot_bytes(width=800, height=600, max_iter=200, center=( -0.5, 0.0 ),
  scale=1.5, seed=None, palette="warm") -> bytes (PNG)

Implementation details
- Uses a straightforward numpy-vectorized iteration to compute escape counts.
- Builds a simple palette from the seed so outputs vary nicely.
- Overlays a small parameter legend on the image so it becomes a "snapshot".
"""

from typing import Tuple, Optional
import io
import math
import random

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except Exception as e:  # Lazy import handling; callers should present useful error if missing
    np = None
    Image = None
    ImageDraw = None
    ImageFont = None


def _build_palette(n: int, seed: Optional[int] = None, style: str = "warm"):
    """Return an (n,3) uint8 palette influenced by seed and style."""
    rng = random.Random(seed)
    palette = np.zeros((n, 3), dtype=np.uint8)

    # Base hues for different styles
    if style == "cool":
        base = rng.uniform(0.5, 0.8)  # bluish
    elif style == "mono":
        base = rng.uniform(0.0, 0.2)
    else:
        base = rng.uniform(0.0, 0.4)  # warm-ish default

    for i in range(n):
        t = i / max(1, n - 1)
        # create a smooth variation using sines for pleasing gradients
        r = 0.5 + 0.5 * math.sin(2.0 * math.pi * (base + 0.8 * t) + rng.uniform(-0.3, 0.3))
        g = 0.5 + 0.5 * math.sin(2.0 * math.pi * (base + 0.2 * t) + rng.uniform(-0.3, 0.3))
        b = 0.5 + 0.5 * math.sin(2.0 * math.pi * (base - 0.4 * t) + rng.uniform(-0.3, 0.3))

        # apply contrast and gamma-like curve
        r = int(max(0, min(255, ((r ** 1.2) * 255))))
        g = int(max(0, min(255, ((g ** 1.2) * 255))))
        b = int(max(0, min(255, ((b ** 1.2) * 255))))
        palette[i] = (r, g, b)

    return palette


def generate_mandelbrot_bytes(
    width: int = 800,
    height: int = 480,
    max_iter: int = 200,
    center: Tuple[float, float] = (-0.5, 0.0),
    scale: float = 1.5,
    seed: Optional[int] = None,
    palette_style: str = "warm",
) -> bytes:
    """
    Generate a PNG image of a Mandelbrot-like set and return raw bytes.

    Parameters
    - width, height: output image size
    - max_iter: iteration cap (controls detail)
    - center: (x, y) center in complex plane
    - scale: zoom factor (larger -> wider view); typical 0.5..2.5
    - seed: optional integer to randomize palette and slight jitter
    - palette_style: "warm" (default), "cool", or "mono"

    Returns: PNG bytes
    """
    if np is None or Image is None:
        raise RuntimeError("Missing dependencies: numpy and pillow are required to generate images.")

    rng = random.Random(seed)

    # Compute complex plane bounds keeping aspect ratio
    aspect = width / float(height)
    re_center, im_center = float(center[0]), float(center[1])
    re_span = scale * aspect
    im_span = scale

    re_min = re_center - re_span
    re_max = re_center + re_span
    im_min = im_center - im_span
    im_max = im_center + im_span

    # Create complex grid
    re = np.linspace(re_min, re_max, width, dtype=np.float64)
    im = np.linspace(im_max, im_min, height, dtype=np.float64)  # top-to-bottom
    Re, Im = np.meshgrid(re, im)
    C = Re + 1j * Im

    # Iteration arrays
    Z = np.zeros_like(C, dtype=np.complex128)
    counts = np.zeros(C.shape, dtype=np.int32)
    mask = np.ones(C.shape, dtype=bool)

    # Vectorized escape-time algorithm
    for i in range(1, max_iter + 1):
        Z[mask] = Z[mask] * Z[mask] + C[mask]
        escaped = np.greater(np.abs(Z), 2.0)
        newly = escaped & mask
        counts[newly] = i
        mask &= ~newly
        if not mask.any():
            break

    # Normalize counts to 0..max_iter
    norm = counts.astype(np.float32) / float(max_iter)
    # Smooth coloring trick (optional): add log-smoothing where escaped
    with np.errstate(divide="ignore", invalid="ignore"):
        nz = counts > 0
        # compute continuous index for smoother gradients
        cont = np.zeros_like(norm)
        cont[nz] = (counts[nz] + 1 - np.log(np.log(np.abs(Z[nz])))/np.log(2.0)) / float(max_iter)
        # blend discrete and continuous for variety
        blend = 0.6
        final = (1.0 - blend) * norm + blend * cont
        final = np.clip(final, 0.0, 1.0)

    # Build palette and map to RGB
    palette_size = max(64, min(1024, max_iter))
    palette = _build_palette(palette_size, seed=seed, style=palette_style)

    # Map final normalized values into palette indices
    indices = (final * (palette_size - 1)).astype(np.int32)
    rgb = palette[indices]

    # Create PIL image
    img = Image.fromarray(rgb.astype("uint8"), mode="RGB")

    # Overlay small caption/legend showing parameters (so image becomes a snapshot)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    caption = f"iter={max_iter} center=({re_center:.3f},{im_center:.3f}) scale={scale:.3f} seed={seed}"
    text_w, text_h = draw.textsize(caption, font=font) if font else (len(caption) * 6, 10)

    padding = 6
    rect_w = text_w + padding * 2
    rect_h = text_h + padding * 2
    # Draw semi-transparent background (approximation since mode=RGB)
    bg = (0, 0, 0)
    fg = (255, 255, 255)
    # place in bottom-left
    x0 = 6
    y0 = height - rect_h - 6
    draw.rectangle([x0, y0, x0 + rect_w, y0 + rect_h], fill=bg)
    draw.text((x0 + padding, y0 + padding), caption, fill=fg, font=font)

    # Slight vignette to make images look "stunning"
    try:
        vignette = Image.new("L", (width, height), 0)
        vd = np.linspace(0.0, 1.0, max(width, height))
        # radial mask
        X = np.linspace(-1, 1, width)[None, :]
        Y = np.linspace(-1, 1, height)[:, None]
        R = np.sqrt(X * X + Y * Y)
        mask_v = np.clip(1.0 - R, 0.0, 1.0)
        mask_v = (mask_v ** 1.2) * 255.0
        vignette = Image.fromarray(mask_v.astype("uint8"), mode="L")
        img.putalpha(vignette)
        # convert back to RGB blended on black to simulate vignette
        bg_img = Image.new("RGB", (width, height), (0, 0, 0))
        bg_img.paste(img, mask=img.split()[-1])
        final_img = bg_img
    except Exception:
        final_img = img

    # Output PNG bytes
    bio = io.BytesIO()
    final_img.save(bio, format="PNG", optimize=True)
    bio.seek(0)
    return bio.getvalue()
