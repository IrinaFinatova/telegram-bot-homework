class RequestException(KeyError):
    pass


class RequestAPINotOK(RequestException):
    pass


class HomeworkDictNotExist(RequestException):
    pass


class HomeworkDictEmpty(RequestException):
    pass


class HomeworkDictTypeError(RequestException):
    pass


class StatusNotExist(RequestException):
    pass
