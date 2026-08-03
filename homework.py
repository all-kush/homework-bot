import logging
import os
import requests
from telebot import TeleBot
from dotenv import load_dotenv
import time
import sys
from exceptions import (
    MissingTokensError,
    APIRequestError,
    UnknownStatusError
)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.DEBUG,
    encoding='utf-8',
    handlers=[logging.StreamHandler(sys.stdout)]
)


def check_tokens():
    """Проверяет наличие всех переменных окружения."""
    missed_ones = []
    variables = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    for name, value in variables.items():
        if not value:
            missed_ones.append(name)
    if missed_ones:
        logging.critical(
            f'Некоторые переменные окружения отсутствуют: '
            f'{", ".join(missed_ones)}')
        raise MissingTokensError(
            'Невозможно продолжить: отсутствуют переменные окружения.')


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logging.debug(f'Бот отправил сообщение "{message}"')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Отправляет запрос к API и возвращает ответ."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params=params)
        if response.status_code != 200:
            raise APIRequestError(
                f'Эндпоинт {ENDPOINT} недоступен. '
                f'Код ответа: {response.status_code}')
        return response.json()
    except Exception as error:
        logging.error(f'Эндпоинт {ENDPOINT} недоступен. Ошибка: {error}')
        raise APIRequestError(
            f'Эндпоинт {ENDPOINT} недоступен. Ошибка: {error}')


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logging.error('Ответ API не является словарем')
        raise TypeError('Ожидался словарь!')
    if 'homeworks' not in response:
        logging.error('В ответе API нет ключа "homeworks"')
        raise ValueError('В ответе нет ключа "homeworks"')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        logging.error('Ключ "homeworks" не является списком')
        raise TypeError(
            f'Ключ "homeworks" должен содержать список, '
            f'а не {type(homeworks)}')

    for homework in homeworks:
        if not isinstance(homework, dict):
            logging.error('Элемент списка homeworks не является словарем')
            raise TypeError(
                'Ожидался словарь с данными домашней работы')
        required_fields = ('id', 'lesson_name', 'status')
        for field in required_fields:
            if field not in homework:
                logging.error(f'В домашней работе отсутствует \
                              обязательное поле {field}')
                raise ValueError(f'В домашней работе отсутствует \
                                 обязательное поле {field}')
        if homework['status'] not in HOMEWORK_VERDICTS:
            logging.error(f'Неизвестный статус домашней работы:\
                              {homework["status"]}')
            raise UnknownStatusError(f'Неизвестный статус домашней работы:\
                              {homework["status"]}')


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('Отсутствует ключ "homework_name"')
    if homework_status is None:
        raise KeyError('Отсутствует ключ "status"')
    if homework_status not in HOMEWORK_VERDICTS:
        logging.error('Неизвестный статус домашней работы: {homework_status}')
        raise UnknownStatusError(f'Неизвестный статус домашней работы: \
                       {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error = None

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response['homeworks']
            if homeworks:
                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)
            else:
                logging.debug('Нет новых статусов.')
            timestamp = int(time.time())
            last_error = None

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if last_error != message:
                send_message(bot, message)
                last_error = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
