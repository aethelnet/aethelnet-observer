"""
Chart handler mixin that generates a Mandelbrot-like snapshot and sends it via Telegram.

Usage:
- Command: /chart [width] [height] [iters] [scale] [seed]
  Examples:
    /chart
    /chart 640 360 250 1.2 42

Dependencies:
- This file calls generate_mandelbrot_bytes from services.chart.mandelbrot,
  which requires numpy and pillow. If dependencies are missing, the handler informs the user.

Notes:
- This file is safe to add as a new mixin. Register its cmd_chart method wherever your bot
  registers command handlers. It follows the async interface used elsewhere in the project.
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging
import io

logger = logging.getLogger("TelegramBot")

try:
    from services.chart.mandelbrot import generate_mandelbrot_bytes
except Exception as e:
    generate_mandelbrot_bytes = None  # handler will return an error if called without generator


class ChartMixin:
    async def cmd_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Generate a fractal snapshot and send it as a photo.

        Accepts optional args: width height iterations scale seed
        """
        message = update.effective_message
        # Defaults
        width = 800
        height = 480
        iterations = 200
        scale = 1.5
        seed = None

        # Parse args if present
        try:
            args = context.args or []
            if len(args) >= 1:
                width = int(args[0])
            if len(args) >= 2:
                height = int(args[1])
            if len(args) >= 3:
                iterations = int(args[2])
            if len(args) >= 4:
                scale = float(args[3])
            if len(args) >= 5:
                seed = int(args[4])
        except Exception as e:
            logger.debug(f"Chart parse error: {e}")

        if generate_mandelbrot_bytes is None:
            await message.reply_text("Chart generator unavailable. Missing dependencies or import error.")
            return

        try:
            img_bytes = generate_mandelbrot_bytes(
                width=width,
                height=height,
                max_iter=iterations,
                scale=scale,
                seed=seed,
            )
        except RuntimeError as e:
            await message.reply_text(str(e))
            return
        except Exception as e:
            logger.exception("Unexpected error generating chart")
            await message.reply_text(f"[ERROR] Could not generate chart: {e}")
            return

        bio = io.BytesIO(img_bytes)
        bio.name = "chart.png"
        bio.seek(0)

        caption = f"Fractal Snapshot — {width}x{height} iters={iterations} scale={scale} seed={seed}"
        try:
            await message.reply_photo(photo=bio, caption=caption)
        except Exception:
            # fallback: if callback_query context
            try:
                await update.callback_query.message.reply_photo(photo=bio, caption=caption)
            except Exception as e:
                logger.error(f"Failed to send chart image: {e}")
                await message.reply_text("[ERROR] Failed to send generated chart.")
