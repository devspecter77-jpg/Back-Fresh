import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
_ADMIN_ID_RAW = os.getenv("ADMIN_ID")
ADMIN_CONTACT = os.getenv("ADMIN_CONTACT")
PAYMENT_CARD = os.getenv("PAYMENT_CARD")
FREE_ATTEMPTS = int(os.getenv("FREE_ATTEMPTS", "5"))
PRICE_SOM = os.getenv("PRICE_SOM", "10")
PRICE_ATTEMPTS = os.getenv("PRICE_ATTEMPTS", "60")
REMBG_MODEL = os.getenv("REMBG_MODEL", "u2net")

BASE_DIR = Path(__file__).resolve().parent.parent
# Railway kabi platformalarda konteyner qayta ishga tushganda fayllar o'chib ketadi —
# doimiy Volume ulangan bo'lsa, APP_DATA_DIR shu Volume yo'liga (masalan /data) ko'rsatilishi kerak.
DATA_ROOT = Path(os.getenv("APP_DATA_DIR", BASE_DIR))
STORAGE_DIR = DATA_ROOT / "storage"
BG_DIR = STORAGE_DIR / "backgrounds"
TMP_DIR = STORAGE_DIR / "tmp"
DATA_DIR = DATA_ROOT / "data"
DB_PATH = str(DATA_DIR / "bot.db")

for _dir in (BG_DIR, TMP_DIR, DATA_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

_required = {
    "BOT_TOKEN": BOT_TOKEN,
    "ADMIN_ID": _ADMIN_ID_RAW,
    "ADMIN_CONTACT": ADMIN_CONTACT,
    "PAYMENT_CARD": PAYMENT_CARD,
}
_missing = [name for name, value in _required.items() if not value]
if _missing:
    raise RuntimeError(
        ".env faylida quyidagi qiymatlar to'ldirilmagan: "
        + ", ".join(_missing)
        + ". .env.example faylidan nusxa ko'chirib .env deb saqlang va o'z qiymatlaringiz bilan to'ldiring."
    )

ADMIN_ID = int(_ADMIN_ID_RAW)
