from btcturk_api.exceptions import BTCTurkAuthenticationError
from requests import Response
import functools


def authentication_required(func):
    @functools.wraps(func)
    def wrapper_decorator(*args, **kwargs):
        if not args[0].authenticated:
            raise BTCTurkAuthenticationError(response=Response())
        value = func(*args, **kwargs)
        return value

    return wrapper_decorator
