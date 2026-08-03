class HomeworkBotError(Exception):
    """Базовое исключение для всех ошибок бота."""
    pass


class MissingTokensError(HomeworkBotError):
    """Выбрасывается при отсутствии обязательных переменных окружения."""
    pass


class APIRequestError(HomeworkBotError):
    """Выбрасывается при проблемах с запросом к API."""
    pass


class UnknownStatusError(HomeworkBotError):
    """Выбрасывается при получении неизвестного статуса."""
    pass
