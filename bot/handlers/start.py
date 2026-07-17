from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot import db
from bot.config import ADMIN_ID, FREE_ATTEMPTS
from bot.keyboards import contact_keyboard, main_menu_keyboard
from bot.states import Registration

router = Router()

WELCOME = (
    "\U0001F44B Assalomu alaykum!\n\n"
    "Bu bot orqali rasmning orqa fonini olib tashlashingiz va istalgan fonni qo'shishingiz mumkin.\n\n"
    "Sizning ID: <code>{chat_id}</code>"
)

MENU_TEXT = "Quyidagi bo'limlardan birini tanlang.\n\U0001F39F Qolgan urinishlar: <b>{attempts}</b>"


async def show_menu(message: Message, chat_id: int) -> None:
    user = await db.get_user(chat_id)
    attempts = user["attempts_left"] if user else 0
    await message.answer(MENU_TEXT.format(attempts=attempts), reply_markup=main_menu_keyboard())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await db.get_user(message.chat.id)

    if user is None:
        await message.answer(WELCOME.format(chat_id=message.chat.id))
        await message.answer(
            "Ro'yxatdan o'tish uchun telefon raqamingizni yuboring \U0001F447",
            reply_markup=contact_keyboard(),
        )
        await state.set_state(Registration.waiting_contact)
        return

    if user["is_blocked"]:
        await message.answer("⛔️ Siz botdan foydalanish huquqidan mahrum qilingansiz.")
        return

    await show_menu(message, message.chat.id)


@router.message(Registration.waiting_contact, F.contact)
async def process_contact(message: Message, state: FSMContext) -> None:
    if message.contact.user_id != message.from_user.id:
        await message.answer("Iltimos, faqat o'zingizning raqamingizni yuboring.")
        return

    await db.create_user(message.chat.id, message.contact.phone_number)
    await state.clear()

    await message.answer(
        f"✅ Ro'yxatdan o'tdingiz! Sizga bepul {FREE_ATTEMPTS} ta urinish berildi.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await show_menu(message, message.chat.id)

    if ADMIN_ID:
        try:
            await message.bot.send_message(
                ADMIN_ID,
                "\U0001F195 Yangi foydalanuvchi ro'yxatdan o'tdi\n"
                f"\U0001F4DE Tel: {message.contact.phone_number}\n"
                f"Chat ID: <code>{message.chat.id}</code>",
            )
        except Exception:
            pass


@router.message(Registration.waiting_contact)
async def waiting_contact_fallback(message: Message) -> None:
    await message.answer(
        'Iltimos, pastdagi "\U0001F4F1 Raqamni yuborish" tugmasini bosing.',
        reply_markup=contact_keyboard(),
    )
