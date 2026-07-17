from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_contact = State()


class Flow(StatesGroup):
    waiting_subject = State()
    waiting_bg_choice = State()
    waiting_bg_photo = State()


class AdminFlow(StatesGroup):
    waiting_credit_amount = State()
