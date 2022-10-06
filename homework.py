import logging
import os
import time
import requests
import telegram
from typing import Union, Dict, List

from dotenv import load_dotenv
from exception import RequestAPINotOK, HomeworkDictNotExist, HomeworkDictEmpty, TokenNotExist, HomeworkTypeError, \
    StatusNotExist

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKENS = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """ Проверка доступности токенов(переменных окружения),
                 необходимых для работы бота."""
    for token in TOKENS:
        try:
            os.environ[token]
        except KeyError:
            return False
    return True


def get_api_answer(current_timestamp: int) -> Dict[str, Union[str, int]]:
    """ Запрос к API Яндекс и возврат запроса в формате словаря."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        logging.exception('Статус ответа API НЕ ОК')
        raise RequestAPINotOK(
            f'Статус ответа API response {response.status_code}')
    return response.json()


def check_response(response: Dict[str, Union[str, int]]) -> List[Union[str, int]]:
    """ Возврат списка доступных домашних работ из ответа API по ключу 'homeworks'."""
    print(response)
    print(response['homeworks'])
    print(response['homeworks'][0])
    if not response['homeworks']:
        logging.exception('Ответ API содержит пустой словаь с ключом homeworks')
        raise HomeworkDictEmpty('Нет сданной текущей ДР.')
    if type(response['homeworks']) != list:
        logging.exception('Ответ API не в формате списка ДР')
        raise HomeworkTypeError('В ответе API нет списка ДР')
    return response['homeworks']


def parse_status(homework: List[Union[str, int]]) -> str:
    """ Формирование сообщения для бота о текущем статусе домашней работы"""
    if 'homework_name' and 'status' not in homework:
        logging.exception('Ответ API не содержит нужного ключа')
        raise HomeworkDictNotExist('Нет нужных ключей в списке ДР')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        logging.exception('Неизвестный статус работы')
        raise StatusNotExist('Незнакомый статус домашней работы')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot: telegram.Bot, message: str) -> None:
    try:
        return bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.exception(f'Телеграмм не работает: {error}!')


def main() -> None:
    """Основная логика работы бота."""
    while check_tokens():
        try:
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
            # urrent_timestamp = int(time.time())
            current_timestamp = 1663440442
            response = get_api_answer(current_timestamp)
            homework = check_response(response)[0]
            # print(homework)
            message = parse_status(homework)
            # print(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()
