import io
import logging

from PIL import Image
from rembg import new_session, remove

from bot.config import REMBG_MODEL

logger = logging.getLogger(__name__)

logger.info("rembg modeli yuklanmoqda: %s (birinchi ishga tushirishda yuklab olinishi mumkin)", REMBG_MODEL)
_session = new_session(REMBG_MODEL)


def remove_background(image_bytes: bytes) -> Image.Image:
    """CPU-bog'liq operatsiya — chaqiruvchi tomon asyncio.to_thread orqali chaqirishi kerak."""
    input_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    return remove(
        input_image,
        session=_session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10,
        post_process_mask=True,
    )
