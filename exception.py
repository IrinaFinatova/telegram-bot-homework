class RequestException(KeyError):
    pass


class RequestAPINotOK(RequestException):
    pass


class RequestApiNotWork(RequestException):
    pass


class HomeworkDictNotExist(RequestException):
    pass


class HomeworkDictEmpty(RequestException):
    pass


class StatusNotExist(RequestException):
    pass


