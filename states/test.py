from aiogram.fsm.state import State, StatesGroup

class TestStates(StatesGroup):
    waiting_answer = State()
    completed = State() 