from aiogram.fsm.state import State, StatesGroup


class CalculatorStates(StatesGroup):
    waiting_balance       = State()
    waiting_risk_percent  = State()
    waiting_stoploss_pips = State()
