import io
import logging
import os
from pathlib import Path

from PIL import Image
from rembg import new_session, remove

from bot.config import REMBG_MODEL

logger = logging.getLogger(__name__)

# APP_DATA_DIR berilgan bo'lsa (masalan Railway'da doimiy Volume), rembg modelini
# (~170MB) o'sha yerga yozamiz — aks holda konteyner qayta ishga tushganda model
# har safar qaytadan yuklab olinadi. Lokalda APP_DATA_DIR berilmagani uchun rembg'ning
# o'z standart keshidan (~/.u2net) foydalanadi, qayta yuklashning hojati bo'lmaydi.
_app_data_dir = os.getenv("APP_DATA_DIR")
if _app_data_dir:
    os.environ.setdefault("U2NET_HOME", str(Path(_app_data_dir) / "u2net_models"))

logger.info("rembg modeli yuklanmoqda: %s (birinchi ishga tushirishda yuklab olinishi mumkin)", REMBG_MODEL)
_session = new_session(REMBG_MODEL)

# Telefon kamera rasmlari (masalan 3000x4000px) alpha-matting bilan juda ko'p xotira
# talab qiladi va kichik serverlarda (masalan Railway'ning kichik tarifida) jarayonni
# o'ldirib qo'yishi mumkin. Shuning uchun ishlovdan oldin oqilona o'lchamga kichraytiramiz —
# ko'zga sifat farqi deyarli sezilmaydi, lekin xotira sarfi bir necha barobar kamayadi.
MAX_DIMENSION = int(os.getenv("REMBG_MAX_DIMENSION", "1600"))


def remove_background(image_bytes: bytes) -> Image.Image:
    """CPU-bog'liq operatsiya — chaqiruvchi tomon asyncio.to_thread orqali chaqirishi kerak."""
    input_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    if max(input_image.size) > MAX_DIMENSION:
        input_image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    return remove(
        input_image,
        session=_session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10,
        post_process_mask=True,
    )
