class HomeworkBotError(Exception):
    """Базовое исключение для всех ошибок бота."""


class MissingTokensError(HomeworkBotError):
    """Выбрасывается при отсутствии обязательных переменных окружения."""


class APIRequestError(HomeworkBotError):
    """Выбрасывается при проблемах с запросом к API."""


class UnknownStatusError(HomeworkBotError):
    """Выбрасывается при получении неизвестного статуса."""
