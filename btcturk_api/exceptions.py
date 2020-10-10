from requests import Response, get
from datetime import datetime
import time


class BadRequestError(Exception):
    def __init__(self, response):
        self.response = response
        self.errors = {
            400: InvalidRequestParameterError,
            401: BTCTurkAuthenticationError,
            404: UrlNotFoundError,
            422: RequestProcessingError,
            429: RequestLimitExceededError
        }

        try:
            exception_class = self.errors[response.status_code]
            raise exception_class(response)
        except KeyError:
            raise UnknownError(response)


class InvalidRequestParameterError(Exception):
    def __init__(self, response):
        self.response = response
        self.error_message = response.json()['message']
        print(self.error_message)


class BTCTurkAuthenticationError(Exception):
    def __init__(self, response: Response):
        self.error_msg = "Authentication Error.\n"

        if response.content:
            server_response_message = response.json()['message']
            self.error_msg += f"Server Response: {server_response_message}"
            if server_response_message == "Unauthorized - Invalid Nonce":
                self._add_helper_msg_for_invalid_nonce()
        super().__init__(self.error_msg)

    def _add_helper_msg_for_invalid_nonce(self):
        self.error_msg += "You have encountered Invalid Nonce Error.\nThis usually happens when your client's time and " \
                          "server's time are inconsistent.\n"
        client_time = datetime.now()
        server_time = None
        try:
            server_time_response = get(url="https://api.btcturk.com/api/v2/server/time")
            server_time = datetime.fromtimestamp(server_time_response.json()['serverTime'] / 1000)
        except Exception as e:
            self.error_msg += "Couldn't get server's time."

        if not server_time:
            return self.error_msg

        if client_time < server_time:
            self.error_msg += f"Your computer's time is behind of servers time by {server_time - client_time}"
        else:
            self.error_msg += f"Your computer's time is ahead of servers time by {client_time - server_time}"
        return self.error_msg


class UrlNotFoundError(Exception):
    def __init__(self, response):
        super().__init__(f"There is something wrong with this API address: "
                         f"{response.url}\n The endpoint may be changed. "
                         f"Check the github page for further information")


class RequestProcessingError(Exception):
    def __init__(self, response):
        super().__init__("Request could not be processed.\n"
                         f"{response.content}")


class RequestLimitExceededError(Exception):
    def __init__(self, response):
        super().__init__("Request limit has been exceeded.\n"
                         f"{response.content}")


class InternalServerError(Exception):
    def __init__(self, response):
        super().__init__("Internal Server Error!\n"
                         f"{response.content}")


class UnknownError(Exception):
    def __init__(self, response):
        super().__init__(f"Unknown Response Code: {response.status_code}")
