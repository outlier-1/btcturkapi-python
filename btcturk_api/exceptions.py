from requests import Response


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
        error_msg = "Authentication Error.\n"

        if response.content:
            server_response_message = response.json()['message']
            error_msg += f"Server Response: {server_response_message}"

        super().__init__(error_msg)


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
