from aiogram.fsm.state import State, StatesGroup


class AnalysisStates(StatesGroup):
    waiting_custom_pair = State()
