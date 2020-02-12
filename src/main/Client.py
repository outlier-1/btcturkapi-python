import base64
import hashlib
import hmac

import requests
import time

class Client:

    API_BASE = "https://api.btcturk.com"
    API_ENDPOINT_AUTH = "/api/v1/"
    API_ENDPOINT_NON_AUTH = "/api/v2/"
    API_ENDPOINT_TRANSACTIONS = "/api/v1/users/transactions/"

    def __init__(self, api_key=None, api_secret=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.authenticated = False
        self.session = None

        self._init_session()

        if api_key and api_secret:
            self.authenticate()

    def _init_session(self):
        session = requests.session()
        headers = {
            "Content-Type": "application/json"
        }
        session.headers.update(headers)
        self.session = session

    def _create_public_endpoint_url(self, endpoint):
        return f"{self.API_BASE}{self.API_ENDPOINT_NON_AUTH}{endpoint}"

    def _create_auth_endpoint_url(self, endpoint):
        return f"{self.API_BASE}{self.API_ENDPOINT_AUTH}{endpoint}"

    def _create_signature(self):
        api_secret = base64.b64decode(self.api_secret)
        stamp = str(int(time.time()) * 1000)
        data = "{}{}".format(self.api_key, stamp).encode('utf-8')
        signature = hmac.new(api_secret, data, hashlib.sha256).digest()
        signature = base64.b64encode(signature)
        return signature

    def _update_session_headers(self, **kwargs):
        signature = self._create_signature()
        headers = {
            "X-Stamp": str(int(time.time()) * 1000),
            "X-Signature": str(signature.decode('utf-8')),
        }

        for key, value in kwargs:
            headers[key] = value

        self.session.headers.update(headers)

    # Signature bug: report to btcturk-trader github page
    def authenticate(self):
        url = self._create_auth_endpoint_url('users/balances')
        signature = self._create_signature()
        headers = {
            "X-PCK": self.api_key,
            "X-Stamp": str(int(time.time()) * 1000),
            "X-Signature": str(signature.decode('utf-8')),
        }
        status = requests.get(url, headers=headers).status_code

        if status == 200:
            # Authentication successful, update session header
            self.authenticated = True
            self.session.headers.update({"X-PCK": self.api_key})

    @staticmethod
    def _handle_response(response):
        status = response.status_code
        if status / 100 == 4:
            # Raise bad request error
            pass
        if status / 100 == 5:
            # Raise internal server error
            pass

    def _get(self, url, params=None):
        response = self.session.get(url=url, params=params)
        self._handle_response(response)
        return response.json()['data']

    def _post(self, url, params=None):
        response = self.session.post(url=url, data=json.dumps(params))
        self._handle_response(response)

        if response.json()['success'] == 'false':
            # Raise invalid request parameter exception
            pass

        return response.json()['data']

    def _delete(self, url, params=None):
        response = self.session.delete(url=url, params=params, data=json.dumps(params))
        self._handle_response(response)

        return "SUCCEEDED"
