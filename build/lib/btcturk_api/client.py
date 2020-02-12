from btcturk_api.properties import authentication_required
from btcturk_api.exceptions import BadRequestError, InternalServerError, InvalidRequestParameterError
from btcturk_api.constants import CRYPTO_SYMBOLS, CURRENCY_SYMBOLS, DEPOSIT_OR_WITHDRAWAL, TRADE_TYPES
import base64
import hashlib
import hmac
import json

import requests

import time
import datetime as dt

import uuid


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
            raise BadRequestError(response)

        if status / 100 == 5:
            raise InternalServerError(response)

    def _get(self, url, params=None):
        response = self.session.get(url=url, params=params)
        self._handle_response(response)
        return response.json()['data']

    def _post(self, url, params=None):
        response = self.session.post(url=url, data=json.dumps(params))
        self._handle_response(response)

        if response.json()['success'] == 'false':
            raise InvalidRequestParameterError(response)

        return response.json()['data']

    def _delete(self, url, params=None):
        response = self.session.delete(url=url, params=params, data=json.dumps(params))
        self._handle_response(response)

        return "SUCCEEDED"

    # PUBLIC ENDPOINT IMPLEMENTATIONS

    def tick(self, pair=None, **kwargs):
        request_url = self._create_public_endpoint_url('ticker')
        params = kwargs if kwargs else {}

        if pair:
            return self._get(request_url, {'pairSymbol': pair})
        return self._get(request_url, params)

    def get_order_book(self, pair=None, limit=100, **kwargs):
        request_url = self._create_public_endpoint_url('orderbook')
        params = kwargs if kwargs else {'pairSymbol': pair, 'limit': limit}

        return self._get(request_url, params)

    def get_trades(self, pair=None, last=50, **kwargs):
        request_url = self._create_public_endpoint_url('trades')
        params = kwargs if kwargs else {'pairSymbol': pair, 'last': last}

        return self._get(request_url, params=params)

    # AUTHENTICATION REQUIRED GET ENDPOINT IMPLEMENTATIONS

    @authentication_required
    def get_account_balance(self):
        url = self._create_auth_endpoint_url('users/balances')
        self._update_session_headers()
        balance_list = self._get(url)
        return balance_list

    @authentication_required
    def get_trade_history(self, trade_type=None, symbol='BTC',
                          start_date=None, end_date=int(time.time() * 1000), **kwargs):
        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(dt.datetime.today() - dt.timedelta(days=30))
            start_date = int(last_30_days_timestamp * 1000)

        if not symbol:
            symbol = CRYPTO_SYMBOLS

        if not trade_type:
            trade_type = TRADE_TYPES

        request_url = self.API_BASE + self.API_ENDPOINT_TRANSACTIONS + 'trade'
        params = kwargs if kwargs else {'type': trade_type, 'symbol': symbol, 'startDate': start_date,
                                        'endDate': end_date}

        self._update_session_headers()
        history = self._get(request_url, params)
        return history

    @authentication_required
    def get_crypto_history(self, symbol=None, _type=None, start_date=None, end_date=int(time.time() * 1000), **kwargs):
        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(dt.datetime.today() - dt.timedelta(days=30))
            start_date = int(last_30_days_timestamp * 1000)

        if not symbol:
            symbol = CRYPTO_SYMBOLS

        if not _type:
            _type = DEPOSIT_OR_WITHDRAWAL

        request_url = self.API_BASE + self.API_ENDPOINT_TRANSACTIONS + 'crypto'
        params = kwargs if kwargs else {'type': _type, 'symbol': symbol, 'startDate': start_date, 'endDate': end_date}

        self._update_session_headers()
        history = self._get(request_url, params)
        return history

    @authentication_required
    def get_fiat_history(self, balance_types=None, currency_symbols=None,
                         start_date=None, end_date=int(time.time() * 1000), **kwargs):
        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(dt.datetime.today() - dt.timedelta(days=3600))
            start_date = int(last_30_days_timestamp * 1000)

        if not balance_types:
            balance_types = DEPOSIT_OR_WITHDRAWAL

        if not currency_symbols:
            currency_symbols = CURRENCY_SYMBOLS

        request_url = self.API_BASE + self.API_ENDPOINT_TRANSACTIONS + 'fiat'
        params = kwargs if kwargs else {'balanceTypes': balance_types, 'currencySymbols': currency_symbols,
                                        'startDate': start_date, 'endDate': end_date}

        self._update_session_headers()
        history = self._get(request_url, params)
        return history

    @authentication_required
    def get_open_orders(self, pair=None, **kwargs):
        request_url = self._create_auth_endpoint_url('openOrders')
        params = kwargs if kwargs else {'pairSymbol': pair}

        self._update_session_headers()
        orders = self._get(request_url, params)
        return orders

    # AUTHENTICATION REQUIRED ORDER IMPLEMENTATIONS
    @authentication_required
    def cancel_order(self, order_id=None):
        request_url = self._create_auth_endpoint_url('order')
        params = {'id': order_id}

        self._update_session_headers()
        self._delete(request_url, params)

    @authentication_required
    def submit_market_order(self, quantity=0.0, order_type=None,
                            pair_symbol=None, new_order_client_id=None):
        if not new_order_client_id:
            new_order_client_id = str(uuid.uuid1())
        params = {'quantity': quantity, 'newOrderClientId': new_order_client_id, 'orderMethod': 'market',
                  'orderType': order_type, 'pairSymbol': pair_symbol}
        return self.submit_order(params)

    @authentication_required
    def submit_limit_order(self, quantity=0.0, price=0.0, order_type=None,
                           pair_symbol=None, new_order_client_id=None):
        if not new_order_client_id:
            new_order_client_id = str(uuid.uuid1())
        params = {'quantity': quantity, 'price': price, 'newOrderClientId': new_order_client_id, 'orderMethod': 'limit',
                  'orderType': order_type, 'pairSymbol': pair_symbol}
        return self.submit_order(params)

    @authentication_required
    def submit_stop_order(self, stop_price=0.0, quantity=0.0, price=0.0, order_type=None,
                          pair_symbol=None, new_order_client_id=None):
        if not new_order_client_id:
            new_order_client_id = str(uuid.uuid1())
        params = {'quantity': quantity, 'price': price, 'stopPrice': stop_price,
                  'newOrderClientId': new_order_client_id, 'orderMethod': 'market', 'orderType': order_type,
                  'pairSymbol': pair_symbol}
        return self.submit_order(params)

    @authentication_required
    def submit_order(self, params=None, **kwargs):
        request_url = self._create_auth_endpoint_url('order')
        self._update_session_headers()

        if kwargs:
            return self._post(request_url, kwargs)
        return self._post(request_url, params)
