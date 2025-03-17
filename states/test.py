from aiogram.fsm.state import State, StatesGroup

class TestStates(StatesGroup):
    waiting_for_answer = State()
    completed = State() 