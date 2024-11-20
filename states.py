from enum import Enum

class BotStates(Enum):
    ASK_AMOUNT = 1
    ASK_TERM = 2
    ASK_RATE = 3
    SHOW_RESULT = 4
