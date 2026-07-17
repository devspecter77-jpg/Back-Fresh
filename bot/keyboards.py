from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="\U0001F4F1 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="\U0001F5D1 Fonni olib tashlash", callback_data="action:remove")],
            [InlineKeyboardButton(text="\U0001F5BC Fon qo'shish", callback_data="action:add")],
            [InlineKeyboardButton(text="\U0001F501 Fonni olib tashlab, yangisini qo'yish", callback_data="action:both")],
            [InlineKeyboardButton(text="⚙️ Orqa fonni sozlash", callback_data="action:config")],
        ]
    )


def bg_choice_keyboard(has_saved: bool) -> InlineKeyboardMarkup:
    rows = []
    if has_saved:
        rows.append(
            [InlineKeyboardButton(text="\U0001F5BC Saqlangan fondan foydalanish", callback_data="bg:saved")]
        )
    rows.append([InlineKeyboardButton(text="\U0001F4E4 Yangi fon yuborish", callback_data="bg:new")])
    rows.append([InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="bg:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="cancel")]]
    )
