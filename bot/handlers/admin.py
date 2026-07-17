from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot import db
from bot.config import ADMIN_ID
from bot.states import AdminFlow

router = Router()
router.message.filter(F.from_user.id == ADMIN_ID)
router.callback_query.filter(F.from_user.id == ADMIN_ID)

PAGE_SIZE = 5

ADMIN_PANEL_TEXT = "\U0001F6E0 Admin panel"

HELP_TEXT = (
    "❓ Admin buyruqlari:\n"
    "/admin — admin panelni ochish\n"
    "/addcredit <chat_id> <son> — foydalanuvchiga urinish qo'shish\n"
    "/block <chat_id> — foydalanuvchini bloklash\n"
    "/unblock <chat_id> — blokdan chiqarish\n"
    "/userinfo <chat_id> — foydalanuvchi haqida ma'lumot\n"
    "/stats — umumiy statistika"
)


def _panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="\U0001F465 Foydalanuvchilar", callback_data="admin:users:0")],
            [InlineKeyboardButton(text="\U0001F4CA Statistika", callback_data="admin:stats")],
            [InlineKeyboardButton(text="❓ Buyruqlar", callback_data="admin:help")],
        ]
    )


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="\U0001F519 Panel", callback_data="admin:panel")]]
    )


async def _render_users_page(offset: int) -> tuple[str, InlineKeyboardMarkup]:
    total, _ = await db.get_stats()
    users = await db.list_users(offset, PAGE_SIZE)

    if not users:
        return "Foydalanuvchilar topilmadi.", _back_keyboard()

    lines = [f"\U0001F465 Foydalanuvchilar ({offset + 1}-{offset + len(users)} / {total}):"]
    rows: list[list[InlineKeyboardButton]] = []
    for user in users:
        status = "⛔️ Bloklangan" if user["is_blocked"] else "✅ Faol"
        lines.append(
            f"\n<code>{user['chat_id']}</code> — {user['phone_number']}\n"
            f"\U0001F39F Urinish: {user['attempts_left']} | {status}"
        )
        block_label = "✅ Blokdan chiqarish" if user["is_blocked"] else "⛔️ Bloklash"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"➕ Limit ({user['chat_id']})",
                    callback_data=f"admin:credit:{user['chat_id']}:{offset}",
                ),
                InlineKeyboardButton(
                    text=block_label,
                    callback_data=f"admin:toggleblock:{user['chat_id']}:{offset}",
                ),
            ]
        )
    text = "\n".join(lines)

    nav_row = []
    if offset > 0:
        nav_row.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin:users:{max(0, offset - PAGE_SIZE)}")
        )
    if offset + PAGE_SIZE < total:
        nav_row.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin:users:{offset + PAGE_SIZE}")
        )
    if nav_row:
        rows.append(nav_row)
    rows.append([InlineKeyboardButton(text="\U0001F519 Panel", callback_data="admin:panel")])

    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(ADMIN_PANEL_TEXT, reply_markup=_panel_keyboard())


@router.message(Command("adminhelp"))
async def cmd_adminhelp(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.callback_query(F.data == "admin:panel")
async def cb_panel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(ADMIN_PANEL_TEXT, reply_markup=_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:help")
async def cb_help(callback: CallbackQuery) -> None:
    await callback.message.edit_text(HELP_TEXT, reply_markup=_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def cb_stats(callback: CallbackQuery) -> None:
    total, blocked = await db.get_stats()
    text = f"\U0001F4CA Statistika\n\n\U0001F465 Jami foydalanuvchilar: {total}\n⛔️ Bloklangan: {blocked}"
    await callback.message.edit_text(text, reply_markup=_back_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:users:"))
async def cb_users(callback: CallbackQuery) -> None:
    offset = int(callback.data.split(":")[2])
    text, keyboard = await _render_users_page(offset)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:toggleblock:"))
async def cb_toggle_block(callback: CallbackQuery) -> None:
    _, _, chat_id_s, offset_s = callback.data.split(":")
    chat_id, offset = int(chat_id_s), int(offset_s)

    user = await db.get_user(chat_id)
    if user is None:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return

    await db.set_blocked(chat_id, not user["is_blocked"])
    text, keyboard = await _render_users_page(offset)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer("Bloklandi" if not user["is_blocked"] else "Blokdan chiqarildi")


@router.callback_query(F.data.startswith("admin:credit:"))
async def cb_credit_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, chat_id_s, offset_s = callback.data.split(":")
    chat_id, offset = int(chat_id_s), int(offset_s)

    await state.set_state(AdminFlow.waiting_credit_amount)
    await state.update_data(target_chat_id=chat_id, return_offset=offset)
    await callback.message.answer(
        f"\U0001F464 <code>{chat_id}</code> uchun nechta urinish qo'shmoqchisiz? Sonni yuboring.\n"
        "Bekor qilish uchun /admin bosing."
    )
    await callback.answer()


@router.message(AdminFlow.waiting_credit_amount, F.text)
async def on_credit_amount(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.lstrip("-").isdigit() or int(text) <= 0:
        await message.answer("Iltimos, musbat butun son yuboring (masalan 60).")
        return

    count = int(text)
    data = await state.get_data()
    chat_id = data["target_chat_id"]
    offset = data.get("return_offset", 0)

    user = await db.get_user(chat_id)
    if user is None:
        await message.answer("Foydalanuvchi topilmadi.")
        await state.clear()
        return

    await db.add_credit(chat_id, count)
    await state.clear()
    await message.answer(f"✅ {chat_id} ga {count} ta urinish qo'shildi.")
    try:
        await message.bot.send_message(chat_id, f"\U0001F389 Hisobingizga {count} ta urinish qo'shildi!")
    except Exception:
        pass

    text_page, keyboard = await _render_users_page(offset)
    await message.answer(text_page, reply_markup=keyboard)


@router.message(Command("addcredit"))
async def cmd_addcredit(message: Message, command: CommandObject) -> None:
    args = (command.args or "").split()
    if len(args) != 2 or not args[0].lstrip("-").isdigit() or not args[1].lstrip("-").isdigit():
        await message.answer("Foydalanish: /addcredit <chat_id> <son>")
        return

    chat_id, count = int(args[0]), int(args[1])
    user = await db.get_user(chat_id)
    if user is None:
        await message.answer("Bunday foydalanuvchi topilmadi.")
        return

    await db.add_credit(chat_id, count)
    await message.answer(f"✅ {chat_id} ga {count} ta urinish qo'shildi.")
    try:
        await message.bot.send_message(chat_id, f"\U0001F389 Hisobingizga {count} ta urinish qo'shildi!")
    except Exception:
        pass


@router.message(Command("block"))
async def cmd_block(message: Message, command: CommandObject) -> None:
    args = (command.args or "").split()
    if len(args) != 1 or not args[0].lstrip("-").isdigit():
        await message.answer("Foydalanish: /block <chat_id>")
        return

    chat_id = int(args[0])
    user = await db.get_user(chat_id)
    if user is None:
        await message.answer("Bunday foydalanuvchi topilmadi.")
        return

    await db.set_blocked(chat_id, True)
    await message.answer(f"⛔️ {chat_id} bloklandi.")


@router.message(Command("unblock"))
async def cmd_unblock(message: Message, command: CommandObject) -> None:
    args = (command.args or "").split()
    if len(args) != 1 or not args[0].lstrip("-").isdigit():
        await message.answer("Foydalanish: /unblock <chat_id>")
        return

    chat_id = int(args[0])
    user = await db.get_user(chat_id)
    if user is None:
        await message.answer("Bunday foydalanuvchi topilmadi.")
        return

    await db.set_blocked(chat_id, False)
    await message.answer(f"✅ {chat_id} blokdan chiqarildi.")


@router.message(Command("userinfo"))
async def cmd_userinfo(message: Message, command: CommandObject) -> None:
    args = (command.args or "").split()
    if len(args) != 1 or not args[0].lstrip("-").isdigit():
        await message.answer("Foydalanish: /userinfo <chat_id>")
        return

    chat_id = int(args[0])
    user = await db.get_user(chat_id)
    if user is None:
        await message.answer("Bunday foydalanuvchi topilmadi.")
        return

    blocked_text = "Ha" if user["is_blocked"] else "Yo'q"
    await message.answer(
        f"\U0001F464 ID: <code>{user['chat_id']}</code>\n"
        f"\U0001F4DE Tel: {user['phone_number']}\n"
        f"\U0001F39F Urinishlar: {user['attempts_left']}\n"
        f"⛔️ Bloklangan: {blocked_text}"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    total, blocked = await db.get_stats()
    await message.answer(f"\U0001F465 Jami foydalanuvchilar: {total}\n⛔️ Bloklangan: {blocked}")
