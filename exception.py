class APIRequestException(Exception):
    pass


class RequestAPINotOK(APIRequestException):
    pass


class HomeworkDictEmpty(APIRequestException):
  pass



class TokenNotExist(APIRequestException):
    def __init__(self, token):
        self.token = token
        super().__init__(
            f'Токен {token} не найден в переменных окружения'
        )


class HomeworkTypeError(APIRequestException):
    pass

class HomeworkDictNotExist(APIRequestException):
    pass


class RequestAPINotOK(APIRequestException):
    def __init__(self, response):
        self.response = response
        super().__init__(
            f'Статус ответа API Яндекс {response.status_code} НЕ ОК'
        )


class StatusNotExist(APIRequestException):
    pass

