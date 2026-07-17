import asyncio
import io
from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from PIL import Image

from bot import db
from bot.config import ADMIN_CONTACT, ADMIN_ID, BG_DIR, PAYMENT_CARD, PRICE_ATTEMPTS, PRICE_SOM, TMP_DIR
from bot.keyboards import bg_choice_keyboard, cancel_keyboard, main_menu_keyboard
from bot.services.bg_compose import compose, flatten_on_white, image_to_bytes
from bot.services.bg_remove import remove_background
from bot.states import Flow

router = Router()

NO_ATTEMPTS_TEXT = (
    "❌ Bepul urinishlaringiz tugadi.\n\n"
    "Davom etish uchun quyidagi karta raqamiga to'lov qiling:\n"
    f"\U0001F4B3 <code>{PAYMENT_CARD}</code>\n\n"
    f"{PRICE_SOM} so'm = {PRICE_ATTEMPTS} ta urinish\n\n"
    "To'lovni amalga oshirgandan so'ng, chek (skrinshot) va quyidagi ID'ingizni "
    f"{ADMIN_CONTACT} ga yuboring — tez orada urinishlaringiz ko'paytiriladi:\n"
    "\U0001F464 ID: <code>{chat_id}</code>"
)

SUBJECT_PROMPTS = {
    "remove": "\U0001F5BC Fonini olib tashlamoqchi bo'lgan rasmni yuboring.",
    "add": (
        "\U0001F5BC Fon qo'shmoqchi bo'lgan rasmni yuboring (orqa foni allaqachon olib tashlangan, "
        "shaffof PNG bo'lsa, uni FAYL/hujjat sifatida yuboring — shaffoflik saqlanib qolishi uchun)."
    ),
    "both": "\U0001F5BC Rasm yuboring — avval fonini olib tashlayman, so'ng yangi fon qo'shaman.",
    "config": "\U0001F5BC Doimiy fon sifatida saqlanadigan rasmni yuboring.",
}


def _subject_path(chat_id: int) -> Path:
    return TMP_DIR / f"{chat_id}_subject.png"


def _newbg_path(chat_id: int) -> Path:
    return TMP_DIR / f"{chat_id}_newbg.png"


def _saved_bg_path(chat_id: int) -> Path:
    return BG_DIR / f"{chat_id}.png"


async def _extract_file_id(message: Message) -> str:
    return message.document.file_id if message.document else message.photo[-1].file_id


async def _download_bytes(message: Message, file_id: str) -> bytes:
    file = await message.bot.get_file(file_id)
    buf = io.BytesIO()
    await message.bot.download_file(file.file_path, destination=buf)
    return buf.getvalue()


async def _send_result(message: Message, image: Image.Image) -> None:
    jpeg_bytes = image_to_bytes(image, "JPEG", quality=95, subsampling=0)
    await message.answer_photo(BufferedInputFile(jpeg_bytes, filename="natija.jpg"), caption="✅ Tayyor!")


async def _show_menu(message: Message, chat_id: int) -> None:
    user = await db.get_user(chat_id)
    attempts = user["attempts_left"] if user else 0
    await message.answer(
        f"Yana nima qilamiz?\n\U0001F39F Qolgan urinishlar: <b>{attempts}</b>",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data.startswith("action:"))
async def on_action_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.split(":", 1)[1]
    chat_id = callback.message.chat.id
    user = await db.get_user(chat_id)

    if user is None:
        await callback.answer("Iltimos, avval /start bosing.", show_alert=True)
        return
    if user["is_blocked"]:
        await callback.answer("Siz bloklangansiz.", show_alert=True)
        return
    if action != "config" and user["attempts_left"] <= 0 and chat_id != ADMIN_ID:
        await callback.message.answer(NO_ATTEMPTS_TEXT.format(chat_id=chat_id))
        await callback.answer()
        return

    await state.clear()
    await state.update_data(action=action)
    await state.set_state(Flow.waiting_bg_photo if action == "config" else Flow.waiting_subject)

    await callback.message.answer(SUBJECT_PROMPTS[action], reply_markup=cancel_keyboard())
    await callback.answer()


@router.callback_query(F.data.in_({"cancel", "bg:cancel"}))
async def on_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    chat_id = callback.message.chat.id
    for path in (_subject_path(chat_id), _newbg_path(chat_id)):
        if path.exists():
            path.unlink()
    await state.clear()
    await callback.message.answer("Bekor qilindi.", reply_markup=main_menu_keyboard())
    await callback.answer()


@router.message(Flow.waiting_subject, F.photo | F.document)
async def on_subject_received(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    action = data.get("action")
    chat_id = message.chat.id

    file_id = await _extract_file_id(message)
    try:
        raw = await _download_bytes(message, file_id)
        image = Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception:
        await message.answer("Rasmni o'qib bo'lmadi. Boshqa fayl bilan urinib ko'ring.")
        return

    if action == "remove":
        status = await message.answer("⏳ Fon olib tashlanmoqda...")
        try:
            result = await asyncio.to_thread(remove_background, raw)
        except Exception:
            await status.edit_text("Xatolik yuz berdi, qayta urinib ko'ring.")
            return
        await db.decrement_attempt(chat_id)
        await state.clear()
        await status.delete()
        flat = flatten_on_white(result)
        await _send_result(message, flat)
        await _show_menu(message, chat_id)
        return

    if action == "both":
        status = await message.answer("⏳ Fon olib tashlanmoqda...")
        try:
            subject = await asyncio.to_thread(remove_background, raw)
        except Exception:
            await status.edit_text("Xatolik yuz berdi, qayta urinib ko'ring.")
            return
        await status.delete()
    else:  # add
        subject = image

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    subject.save(_subject_path(chat_id), format="PNG")

    has_saved = _saved_bg_path(chat_id).exists()
    await state.set_state(Flow.waiting_bg_choice)
    await message.answer("Endi fon tanlang:", reply_markup=bg_choice_keyboard(has_saved))


@router.message(Flow.waiting_subject)
async def on_subject_wrong_type(message: Message) -> None:
    await message.answer("Iltimos, rasm yuboring (yoki fayl/hujjat sifatida).")


@router.callback_query(Flow.waiting_bg_choice, F.data == "bg:saved")
async def on_bg_saved(callback: CallbackQuery, state: FSMContext) -> None:
    chat_id = callback.message.chat.id
    if not _saved_bg_path(chat_id).exists() or not _subject_path(chat_id).exists():
        await callback.answer("Saqlangan fon topilmadi.", show_alert=True)
        return
    await _finalize_composite(callback.message, state, chat_id, _saved_bg_path(chat_id), cleanup_bg=False)
    await callback.answer()


@router.callback_query(Flow.waiting_bg_choice, F.data == "bg:new")
async def on_bg_new(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Flow.waiting_bg_photo)
    await callback.message.answer("\U0001F5BC Yangi fon rasmini yuboring.", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(Flow.waiting_bg_choice)
async def on_bg_choice_wrong_type(message: Message) -> None:
    await message.answer("Iltimos, yuqoridagi tugmalardan birini bosing.")


@router.message(Flow.waiting_bg_photo, F.photo | F.document)
async def on_bg_photo_received(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    action = data.get("action")
    chat_id = message.chat.id

    file_id = await _extract_file_id(message)
    try:
        raw = await _download_bytes(message, file_id)
        bg_image = Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception:
        await message.answer("Rasmni o'qib bo'lmadi. Boshqa fayl bilan urinib ko'ring.")
        return

    if action == "config":
        BG_DIR.mkdir(parents=True, exist_ok=True)
        bg_image.convert("RGB").save(_saved_bg_path(chat_id), format="PNG")
        await state.clear()
        await message.answer(
            '✅ Fon saqlandi! Endi uni "Fon qo\'shish" yoki "Fonni olib tashlab, yangisini qo\'yish" bo\'limlarida ishlatishingiz mumkin.'
        )
        await _show_menu(message, chat_id)
        return

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    bg_image.convert("RGB").save(_newbg_path(chat_id), format="PNG")
    await _finalize_composite(message, state, chat_id, _newbg_path(chat_id), cleanup_bg=True)


@router.message(Flow.waiting_bg_photo)
async def on_bg_wrong_type(message: Message) -> None:
    await message.answer("Iltimos, rasm yuboring (yoki fayl/hujjat sifatida).")


async def _finalize_composite(
    message: Message, state: FSMContext, chat_id: int, bg_path: Path, cleanup_bg: bool
) -> None:
    subj_path = _subject_path(chat_id)
    try:
        subject = Image.open(subj_path).convert("RGBA")
        background = Image.open(bg_path).convert("RGBA")
        result = compose(subject, background)
    except Exception:
        await message.answer("Xatolik yuz berdi, qayta urinib ko'ring.")
        await state.clear()
        return

    await db.decrement_attempt(chat_id)
    await state.clear()

    if subj_path.exists():
        subj_path.unlink()
    if cleanup_bg and bg_path.exists():
        bg_path.unlink()

    await _send_result(message, result)
    await _show_menu(message, chat_id)
