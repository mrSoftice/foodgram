# Constants for models
USERNAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 150
MAX_NAME_LENGTH = 150
MAX_SLUG_LENGTH = 32
COOKING_TIME_MIN_VALUE = 1
COOKING_TIME_FILTERS = {
    'до 10 мин': (0, 10),
    '10-30 мин': (10, 30),
    '30-60 мин': (30, 60),
    'более 60 мин': (60, 0),
}
