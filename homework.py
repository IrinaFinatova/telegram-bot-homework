import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler
from typing import Dict, List, Union

import requests
import telegram
from dotenv import load_dotenv

from exception import (HomeworkDictEmpty, HomeworkDictNotExist,
                       RequestAPINotOK, RequestApiNotWork, RequestException,
                       StatusNotExist, TelegramNotWork)

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, %(name)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens() -> bool:
    """Проверка доступности токенов,необходимых для работы бота."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def get_api_answer(current_timestamp: int) -> Dict[str, Union[str, int]]:
    """Запрос к API Яндекс и возврат запроса в формате словаря."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logger.info('Начинаем запрос к API')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logger.info('Получен запрос с API')
    except RequestException:
        raise RequestApiNotWork('API не работает')
    if response.status_code != HTTPStatus.OK:
        raise RequestAPINotOK(
            f'Статус ответа API response {response.status_code}')
    return response.json()


def check_response(
        response: Dict[str, Union[str, int]]) -> List[Union[str, int]]:
    """Возврат списка доступных ДР из ответа API по ключу 'homeworks'."""
    if not isinstance(response, Dict):
        raise TypeError('Ответ API не содержит словарь')
    if 'current_date' not in response or 'homeworks' not in response:
        raise HomeworkDictEmpty('В словаре ответа API нет нужных ключей!')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, List):
        raise TypeError('В ответе API нет списка ДР')
    return homeworks


def parse_status(homework: Dict[str, Union[str, int]]) -> str:
    """Формирование сообщения для бота о текущем статусе домашней работы."""
    if 'homework_name' not in homework or 'status' not in homework:
        raise HomeworkDictNotExist('Неправильные атрибуты домашней работы!')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise StatusNotExist('Незнакомый статус {homework_status} ДР')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot: telegram.Bot, message: str):
    """Непосредственно отправка сообщения ботом."""
    try:
        logger.info('Начинаем отправку сообщения!')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        raise TelegramNotWork('Телеграмм не работает!')
    else:
        logger.info('Сообщение отправлено!')


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Нет токена! Бот не может работать')
        sys.exit('Поищите ваши токены!')
    logger.info('Начали!')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # current_timestamp = 1663440442
    current_timestamp = int(time.time())
    cache: List[str] = []
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
            else:
                message = 'Пока нет сданной текущей домашней работы!'
        except (RequestException, TypeError) as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message, exc_info=True)
        except Exception as error:
            message = f'Критическая ошибка {error}'
            logger.critical(message, exc_info=True)
        finally:
            if message in cache:
                cache.pop()
            else:
                send_message(bot, message)
                logger.info(f'Отправленное сообщение: {message}')
            cache.append(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
