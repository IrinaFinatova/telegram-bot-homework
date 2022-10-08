import logging
import os
import sys
import time
import requests
import telegram
from exception import *
from typing import Union, Dict, List
from dotenv import load_dotenv
from logging import StreamHandler


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_TIME = 6
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
    if not (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        return False
    return True


def get_api_answer(current_timestamp: int) -> Dict[str, Union[str, int]]:
    """Запрос к API Яндекс и возврат запроса в формате словаря."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        raise RequestAPINotOK(
            f'Статус ответа API response {response.status_code}')
    return response.json()


def check_response(
        response: Dict[str, Union[str, int]]) -> List[Union[str, int]]:
    """Возврат списка доступных ДР из ответа API по ключу 'homeworks'."""
    if not response['homeworks']:
        raise HomeworkDictEmpty('Нет сданной текущей ДР.')
    if type(response['homeworks']) != list:
        raise HomeworkDictTypeError('В ответе API нет списка ДР')
    return response['homeworks']


def parse_status(homework: Dict[str, Union[str, int]]) -> str:
    """Формирование сообщения для бота о текущем статусе домашней работы."""
    if 'homework_name' and 'status' not in homework:
        raise HomeworkDictNotExist('Нет нужных ключей в списке ДР')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise StatusNotExist('Незнакомый статус {homework_status} ДР')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot: telegram.Bot, message: str) -> None:
    """Непосредственно отправка сообщения ботом."""
    return bot.send_message(TELEGRAM_CHAT_ID, message)


cache = []


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Нет токена! Бот не может работать')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # current_timestamp = 1663440442
    current_timestamp = int(time.time())
    while True:
        try:
            logging.info('Начали!')
            response = get_api_answer(current_timestamp)
            homework = check_response(response)[0]
            message = parse_status(homework)
            if message not in cache:
                send_message(bot, message)
                logger.info('Сообщение отправлено')
            else:
                cache.pop()
        except RequestException as error:
            message = f'Сбой в работе программы: {error}'
            if message not in cache:
                logger.error(message, exc_info=True)
                send_message(bot, message)
            else:
                cache.pop()
        except Exception as error:
            message = f'Критическая ошибка {error}'
            if message not in cache:
                logger.critical(message, exc_info=True)
                send_message(bot, message)
            else:
                cache.pop()
        finally:
            time.sleep(RETRY_TIME)
            cache.append(message)


if __name__ == '__main__':
    main()
