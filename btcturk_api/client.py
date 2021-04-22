from btcturk_api.properties import authentication_required
from btcturk_api.exceptions import (
    BadRequestError,
    InternalServerError,
    BTCTurkAuthenticationError,
    BadRespondError,
)
from btcturk_api.constants import (
    CRYPTO_SYMBOLS,
    CURRENCY_SYMBOLS,
    DEPOSIT_OR_WITHDRAWAL,
    TRADE_TYPES,
)

from decimal import Decimal, ROUND_DOWN, InvalidOperation

import base64
import hashlib
import hmac
import json

import requests

import time
import datetime as dt

import uuid


class Client:
    """ API Client Class

    Methods
    -------
    get_exchange_info:
        Method for getting exchange info of any given pair

    get_server_time:
        Gets Current Server Time

    tick:
        Gets price related information of any given pair

    get_ohlc_data:
        Gets daily OHLC data for given pair

    get_order_book:
        Gets the order book of given pair

    get_trades:
        Gets a list of Trades for given pair

    get_account_balance:
        Gets the list of balances which user have

    get_trade_history:
        Gets the history of user's trades.

    get_crypto_history:
        Gets the history of user's crypto transactions.

    get_fiat_history:
        Gets the history of user's fiat transactions.

    get_open_orders:
        Get's list of user's open orders for given pair

    get_all_orders:
        Get's users all orders for given pair

    cancel_order:
        Deletes The Order

    submit_market_order:
        Submits an order in type of 'market order'

    submit_limit_order:
        Submits an order in type of 'limit order'

    submit_stop_order:
        Submits an order in type of 'stop order'
    """

    API_BASE = "https://api.btcturk.com"
    API_ENDPOINT_AUTH = "/api/v1/"
    API_ENDPOINT_NON_AUTH = "/api/v2/"
    API_ENDPOINT_TRANSACTIONS = "/api/v1/users/transactions/"

    def __init__(self, api_key: str = None, api_secret: str = None):
        """ Creates a Client Object with given API Keys

        If user specifies both api_key and secret_key, constructor will try to authenticate the user
        by updating session headers and sending a request to btcturk api with given credentials information.

        Parameters
        ----------
        api_key
            <YOUR BTCTURK API KEY>
        api_secret
            <YOUR BTCTURK API SECRET>
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = self._init_session()
        self.scale_limits = self._get_scale_limits()

        self.authenticated = False

        if api_key and api_secret:
            self._authenticate()

    def _format_unit(self, unit, scale):
        """ Rounds down the unit to given decimal points

        Parameters
        ----------
        unit : float, mandatory
            It might be a price or quantity

        scale: int, mandatory
            Specifies the precision of decimal points

        Returns
        -------
            Decimal
                Decimal object of formatted unit

        Raises
        ------
        ValueError
            If user doesn't provide a valid float input

        """
        try:
            scale_in_decimal_form = Decimal(str(1 / (10 ** scale))) if scale != 0 else Decimal(str(0))
            formatted_unit = Decimal(str(unit)).quantize(scale_in_decimal_form, rounding=ROUND_DOWN)
            return formatted_unit
        except InvalidOperation as e:
            raise ValueError(f"Error occurred while trying to format your input '{unit}'. "
                             f"Make sure you're entering a valid float number")

    def _get_scale_limits(self):
        """ Gets Currency Scales For Price and Amount

        Returns
        -------
        dict
            Each object in this dictionary has this format::

        {
            'exchangeName': {
                'price_scale': <PRICE_SCALE>,
                'amount_scale': <AMOUNT_SCALE>,
                'has_fraction': True/False
            },
            'exchangeName2': {...}
        }

        Raises
        ------
        BadRespondError
            If response doesn't have proper dictionary keys

        """

        request_url = self._create_public_endpoint_url("server/exchangeinfo")
        response = self.session.get(url=request_url)
        self._handle_response(response)

        try:
            scale_limits = {}
            for scale_info in response.json()["data"]["symbols"]:
                name = scale_info["name"]
                name_normalized = scale_info["nameNormalized"]
                price_scale = scale_info["denominatorScale"]
                amount_scale = scale_info["numeratorScale"]
                has_fraction = scale_info["hasFraction"]

                scale_limits[name] = {
                    "price_scale": price_scale,
                    "amount_scale": amount_scale,
                    "has_fraction": has_fraction,
                }
                scale_limits[name_normalized] = scale_limits[name]

            return scale_limits
        except KeyError:
            raise BadRespondError(
                "Server didn't respond properly when requesting scale limits."
            )

    @staticmethod
    def _init_session():
        """ Initializes a session object with necessary headers

        Returns
        -------
        requests.Session
            Session instance with some headers
        """

        session = requests.session()
        headers = {"Content-Type": "application/json"}
        session.headers.update(headers)
        return session

    def _create_public_endpoint_url(self, endpoint):
        """ Constructs Public Endpoint Url

        Parameters
        ----------
        endpoint : str, optional

        Returns
        -------
        str
            url with format https://api.btcturk.com/api/v2/<endpoint>
        """
        return f"{self.API_BASE}{self.API_ENDPOINT_NON_AUTH}{endpoint}"

    def _create_auth_endpoint_url(self, endpoint):
        """ Constructs Auth Required Endpoint Url

        Parameters
        ----------
        endpoint : optional

        Returns
        -------
        str
            url with format https://api.btcturk.com/api/v1/<endpoint>
        """
        return f"{self.API_BASE}{self.API_ENDPOINT_AUTH}{endpoint}"

    def _create_signature(self):
        """ Creates HMAC-SHA256 encoded message
        The HMAC-SHA256 code generated using a private key that contains a timestamp as nonce and api_key

        Returns
        -------
        bytes
            HMAC-SHA256 code
        """
        api_secret = base64.b64decode(self.api_secret)
        stamp = str(int(time.time()) * 1000)
        data = "{}{}".format(self.api_key, stamp).encode("utf-8")
        signature = hmac.new(api_secret, data, hashlib.sha256).digest()
        signature = base64.b64encode(signature)
        return signature

    def _update_session_headers(self, **kwargs):
        """ Updates Client's session's headers with correct signature

        This is important because before each call to authentication required endpoints,
        HMAC-SHA256 message, which is time dependent, should be in headers for authorization.

        Parameters
        ----------
        kwargs : kwargs
            any key, value pair that will be added to header

        """
        signature = self._create_signature()
        headers = {
            "X-Stamp": str(int(time.time()) * 1000),
            "X-Signature": str(signature.decode("utf-8")),
        }

        for key, value in kwargs:
            headers[key] = value

        self.session.headers.update(headers)

    # Signature bug: report to btcturk-trader github page
    def _authenticate(self):
        """ Authenticates the Client

        Authenticates the clients by using api_key and api_sec attributes
        We need to provide 3 parameters for authentication:

        "X-PCK": API Public Key
        "X-Stamp": Nonce
        "X-Signature": Signature

        Nonce is current timestamp in milliseconds

        Signature is a HMAC-SHA256 encoded message. The HMAC-SHA256 code must be generated using a private key
        that contains a timestamp as nonce and your API key

        If authentication succeed, updates the session's header. raises BTCTurkAuthenticationError otherwise

        Raises
        ------
        BTCTurkAuthenticationError
            Authentication Error with Response Message
        """

        url = self._create_auth_endpoint_url("users/balances")
        signature = self._create_signature()
        headers = {
            "X-PCK": self.api_key,
            "X-Stamp": str(int(time.time()) * 1000),
            "X-Signature": str(signature.decode("utf-8")),
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            # Authentication successful, update session header
            self.authenticated = True
            self.session.headers.update({"X-PCK": self.api_key})
        else:
            raise BTCTurkAuthenticationError(response)

    @staticmethod
    def _handle_response(response):
        """ Handles Incoming Responses

        Looks for bad responses and raises proper exceptions

        Parameters
        ----------
        response : requests.Response, mandatory

        Raises
        ----------
        BadRequestError
            If response code has 4xx format

        InternalServerError
            If response code has 5xx format
        """

        status = response.status_code
        if status // 100 == 4:
            raise BadRequestError(response)

        if status // 100 == 5:
            raise InternalServerError(response)

    def _get(self, url, params=None):
        """ Wrapper for HTTP Get Method

        Before returning any object, it gives the response to handler, handler checks for any client or server
        based errors have occurred or not. If didn't occur, returns the data section of response.json()

        Parameters
        ----------
        url : str, mandatory
            Destination URL

        params : dict, optional
            request parameters

        Returns
        -------
        dict
            Response's data section
        """

        response = self.session.get(url=url, params=params)
        self._handle_response(response)
        return response.json()["data"]

    def _post(self, url, params=None):
        """ Wrapper for HTTP Post Method

        Before returning any object, it gives the response to handler, handler checks for any client or server
        based errors have occurred or not. If didn't occur, returns the data section of response.json()

        Parameters
        ----------
        url : str, mandatory
            Destination URL

        params : dict, optional
            request parameters

        Returns
        -------
        dict
            Response's data section
        """

        response = self.session.post(url=url, data=json.dumps(params))
        self._handle_response(response)

        return response.json()["data"]

    def _delete(self, url, params=None):
        """ Wrapper for HTTP Delete Method

        Parameters
        ----------
        url : mandatory
            Destination URL

        params : optional
            request parameters

        Returns
        -------
        bool
            Success value if there is no exception raised by handler
        """
        response = self.session.delete(url=url, params=params, data=json.dumps(params))
        self._handle_response(response)

        return response.json()["success"]

    # ############# PUBLIC ENDPOINT IMPLEMENTATIONS ############# #

    def get_exchange_info(self, symbol_list=None):
        """ Method for getting exchange info of any given pair

        Parameters
        ----------
        symbol_list : list, optional
            In format of ['BTCUSDT', 'XRPUSDT', 'ETHTRY' ...]

        Returns
        -------
        list
            If symbol_list is None, list of data dictionaries of all pairs.
            Otherwise, that list filtered down to given symbol list

            Example of Response Format

            .. code-block:: python

                [
                  {
                    'id': '',
                    'name': '',
                    'nameNormalized': '',
                    'status': '',
                    'numerator': '',
                    'denominator': '',
                    'numeratorScale': '',
                    'denominatorScale': '',
                    'hasFraction': '',
                    'filters': ''
                    'orderMethods': ['MARKET', 'LIMIT', 'STOP_MARKET', 'STOP_LIMIT'], # IMPORTANT
                    'displayFormat': '#,###',
                    'commissionFromNumerator': False, 'order': 999,
                    'priceRounding': False
                  },
                  ...
                ]
        """

        request_url = self._create_public_endpoint_url("server/exchangeinfo")
        exchange_list = self._get(request_url)["symbols"]

        if not symbol_list:
            return exchange_list

        filtered_list = list(
            filter(lambda symbol: symbol["name"] in symbol_list, exchange_list)
        )
        return filtered_list

    def get_server_time(self):
        """ Gets Current Server Time

        Returns
        -------
        dictionary
            Example of Response Format

            .. code-block:: python

                {
                    'serverTime': '<Unix Timestamp as int>',
                    'serverTime2': '<Datetime string>',
                }
        """

        request_url = self._create_public_endpoint_url("server/time")
        response = self.session.get(url=request_url)
        self._handle_response(response)
        response_as_json = response.json()

        return response_as_json

    def tick(self, pair=None, **kwargs):
        """ Gets price related information of any given pair

        If you specify kwargs, the other parameters will be **overridden.**
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        pair : str, optional
            pair symbol like 'BTC_TRY', 'ETH_BTC', ...

        kwargs

        Returns
        -------
        list
            If pair is set, a list of data dictionary with given pair, (length=1)
            Otherwise, a list of data dictionaries of all pairs.

            Example of Response Format

            .. code-block:: python

                [
                  {
                    'pairSymbol': '<Requested pair symbol>',
                    'pairSymbolNormalized': '<Requested pair symbol with "_" in between.>',
                    'timestamp': '<Current Unix time in milliseconds>'
                    'last': '<Last price>',
                    'high': '<Highest trade price in last 24 hours>',
                    'low': '<Lowest trade price in last 24 hours>',
                    'bid': '<Highest current bid>',
                    'ask': '<Lowest current ask>',
                    'open': '<Price of the opening trade in last 24 hours>',
                    'volume': '<Total volume in last 24 hours>',
                    'average': '<Average Price in last 24 hours>',
                    'daily': '<Price change in last 24 hours>',
                    'dailyPercent': '<Price change percent in last 24 hours>',
                    'denominatorSymbol': '<Denominator currency symbol of the pair>',
                    'numeratorSymbol': '<Numerator currency symbol of the pair>',
                  },
                  ...
                ]
        """

        request_url = self._create_public_endpoint_url("ticker")
        params = kwargs if kwargs else {}

        if pair:
            return self._get(request_url, {"pairSymbol": pair})
        return self._get(request_url, params)

    def get_ohlc_data(self, pair=None, last=10, **kwargs):
        """ Gets daily OHLC data for given pair

        If you specify kwargs, the other parameters will be **overridden.**
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        pair : str, optional
            pair symbol like 'BTC_TRY', 'ETH_BTC', ...

        last : int, optional
            number of days

        kwargs

        Returns
        -------
        list
            a list of data dictionary for given pair

            Example of Response Format

            .. code-block:: python

                [
                  {
                    'pairSymbol': '<Requested pair symbol>',
                    'pairSymbolNormalized': '<Requested pair symbol with "_" in between.>',
                    'time': '<Current Unix time in milliseconds>'
                    'open': '<Price of the opening trade on the time>',
                    'high': '<Highest trade price on the time>',
                    'low': '<Lowest trade price on the time>',
                    'close': '<Price of the closing trade on the time>',
                    'volume': '<Total volume on the time>',
                    'average': '<Average price on the time>',
                    'dailyChangeAmount': '<Amount of difference between Close and Open on the Date>',
                    'dailyChangePercentage': '<Percentage of difference between Close and Open on the Date>',
                  },
                  ...
                ]
        """

        request_url = self._create_public_endpoint_url("ohlc")
        params = kwargs if kwargs else {}

        if pair:
            return self._get(request_url, {"pairSymbol": pair, "last": last})
        return self._get(request_url, params)

    def get_order_book(self, pair=None, limit=100, **kwargs):
        """ Gets the order book of given pair

        If you specify kwargs, the other parameters will be **overridden**.
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        pair : str, mandatory
            pair symbol like 'BTC_TRY', 'ETH_BTC', ...

        limit : int, optional
            default 100 max 1000

        kwargs

        Returns
        -------
        dict
            data dictionary

            Example of Response Format

            .. code-block:: python

                [
                  {
                    'timestamp': '<Current Unix time in milliseconds>',
                    'bids': '<Array of current open bids on the orderbook>',
                    'asks': '<Array of current open asks on the orderbook>',
                  },
                  ...
                ]
        """

        request_url = self._create_public_endpoint_url("orderbook")
        params = kwargs if kwargs else {"pairSymbol": pair, "limit": limit}

        return self._get(request_url, params)

    def get_trades(self, pair=None, last=50, **kwargs):
        """ Gets a list of Trades for given pair

        If you specify kwargs, the other parameters will be **overridden.**
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        pair : str, mandatory
            pair symbol like 'BTC_TRY', 'ETH_BTC'..

        last : int, optional
            default 50 max 1000

        Returns
        -------
        dict
            Data dictionary

            Example of Response Format

            .. code-block:: python

                {
                    'pair': '<Requested pair symbol>',
                    'pairNormalized': '<Request Pair symbol with "_" in between.>',
                    'numerator': '<Numerator currency for the requested pair>',
                    'denominator': '<Denominator currency for the requested pair>',
                    'date': '<Unix time of the trade in milliseconds>',
                    'tid': '<Trade ID>',
                    'price': '<Price of the trade>',
                    'amount': '<Amount of the trade>',
                },
        """

        request_url = self._create_public_endpoint_url("trades")
        params = kwargs if kwargs else {"pairSymbol": pair, "last": last}

        return self._get(request_url, params=params)

    # AUTHENTICATION REQUIRED GET ENDPOINT IMPLEMENTATIONS

    @authentication_required
    def get_account_balance(self, assets=None):
        """ Gets the list of balances which user have

        Parameters
        ----------
        assets: optional
            List of assets like ['BTC', 'TRY', ...]

        Returns
        -------
        list
            Example of Response Format

            .. code-block:: python

                [
                  {
                    'asset': 'EUR',
                    'assetname': 'Euro',
                    'balance': '0',
                    'locked': '0',
                    'free': '0',
                    'orderFund': '0',
                    'requestFund': '0',
                    'precision': 2
                  },
                  ...
                ]
        """

        url = self._create_auth_endpoint_url("users/balances")
        self._update_session_headers()
        balance_list = self._get(url)

        if not assets:
            return balance_list

        assets = [asset.upper() for asset in assets]

        filtered_balance_list = list(
            filter(lambda bl: bl["asset"].upper() in assets, balance_list)
        )

        return filtered_balance_list

    @authentication_required
    def get_trade_history(
        self, trade_type=None, symbol=None, start_date=None, end_date=None, **kwargs
    ):
        """ Gets the history of user's trades.

        If trade_type not specified, both 'buy' and 'sell' types will be used

        If symbol not specified, all crypto symbols will be used

        If start_date not specified, it will get trades for last 30 days.

        If you specify kwargs, the other parameters will be **overridden.**
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        trade_type : list, optional
            ["buy", "sell"], ["buy"] or ["sell"]

        symbol : list -> str, optional
            ["btc", "try", ...etc.],

        start_date : timestamp, optional

        end_date : timestamp, optional

        kwargs

        Returns
        -------
        list
            List of trade data dictionaries,

            Example of Response Format

            .. code-block:: python

                [
                  {
                    'price': '<Trade price>',
                    'numeratorSymbol': '<Trade pair numerator symbol>',
                    'denominatorSymbol': '<Trade pair denominator symbol>',
                    'orderType': '<Trade type (buy,sell)>',
                    'id': '<Trade id>',
                    'timestamp': '<Unix timestamp>',
                    'amount': '<Trade Amount (always negative if order type is sell)>',
                    'fee': '<Trade fee>',
                    'tax': '<Trade tax>'
                  },
                  ...
                ]
        """

        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(
                dt.datetime.today() - dt.timedelta(days=30)
            )
            start_date = int(last_30_days_timestamp * 1000)

        if not end_date:
            end_date = int(time.time() * 1000)

        if not symbol:
            symbol = CRYPTO_SYMBOLS

        if not trade_type:
            trade_type = TRADE_TYPES

        request_url = self.API_BASE + self.API_ENDPOINT_TRANSACTIONS + "trade"
        params = (
            kwargs
            if kwargs
            else {
                "type": trade_type,
                "symbol": symbol,
                "startDate": start_date,
                "endDate": end_date,
            }
        )

        self._update_session_headers()
        history = self._get(request_url, params)
        return history

    @authentication_required
    def get_crypto_history(
        self,
        symbol=None,
        transaction_type=None,
        start_date=None,
        end_date=None,
        **kwargs,
    ):
        """ Gets the history of user's crypto transactions.

        If symbol not specified, all crypto symbols will be used

        If transaction_type not specified, both 'withdrawal' and 'deposit' types will be used

        If start_date not specified, it will get trades for last 30 days.

        If you specify kwargs, the other parameters will be **overridden**. Only keyword arguments you specified
        will be used to construct a query. Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        symbol : list, optional
            ["btc", "try", ...etc.]

        transaction_type : list , optional
            ["deposit", "withdrawal"], ["deposit"] or ["withdrawal"]

        start_date : timestamp, optional

        end_date : timestamp, optional

        kwargs

        Returns
        -------
        list
            List of trade data dictionaries,

            Example of Response Format

            .. code-block:: python

                [
                  {
                    'balanceType': '<Type of transaction (deposit, withdrawal)>',
                    'currencySymbol': '<Transaction currency symbol>',
                    'id': '<Transaction id>',
                    'timestamp': '<Unix timestamp>',
                    'funds': '<Funds>',
                    'orderFund': '<Transaction Amount>',
                    'fee': '<Transaction fee>',
                    'tax': <Transaction tax>
                  },
                  ...
                ]
        """

        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(
                dt.datetime.today() - dt.timedelta(days=30)
            )
            start_date = int(last_30_days_timestamp * 1000)

        if not end_date:
            end_date = int(time.time() * 1000)

        if not symbol:
            symbol = CRYPTO_SYMBOLS

        if not transaction_type:
            transaction_type = DEPOSIT_OR_WITHDRAWAL

        request_url = self.API_BASE + self.API_ENDPOINT_TRANSACTIONS + "crypto"
        params = (
            kwargs
            if kwargs
            else {
                "type": transaction_type,
                "symbol": symbol,
                "startDate": start_date,
                "endDate": end_date,
            }
        )

        self._update_session_headers()
        history = self._get(request_url, params)
        return history

    @authentication_required
    def get_fiat_history(
        self,
        balance_types=None,
        currency_symbols=None,
        start_date=None,
        end_date=None,
        **kwargs,
    ):
        """ Gets the history of user's fiat transactions.

        If balance_types not specified, both 'withdrawal' and 'deposit' types will be used

        If currency_symbols not specified, all currency symbols will be used

        If start_date not specified, it will get trades for last 30 days.

        If you specify kwargs, the other parameters will be **overridden**. Only keyword arguments you specified
        will be used to construct a query. Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        balance_types : list, optional
            ["buy", "sell"]

        currency_symbols : list, optional
            ["try", ...etc.]

        start_date : timestamp, optional

        end_date : timestamp, optional

        kwargs

        Returns
        -------
        list
            List of trade data dictionaries,

            Example of Response Format

            .. code-block:: python

                [
                  {
                    'balanceType': '<Type of transaction (deposit, withdrawal)>',
                    'currencySymbol': '<Transaction currency symbol>',
                    'id': '<Transaction id>',
                    'timestamp': '<Unix timestamp>',
                    'funds': '<Funds>',
                    'orderFund': '<Transaction Amount>',
                    'fee': '<Transaction fee>',
                    'tax': <Transaction tax>
                  },
                  ...
                ]
        """
        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(
                dt.datetime.today() - dt.timedelta(days=30)
            )
            start_date = int(last_30_days_timestamp * 1000)

        if not end_date:
            end_date = int(time.time() * 1000)

        if not balance_types:
            balance_types = DEPOSIT_OR_WITHDRAWAL

        if not currency_symbols:
            currency_symbols = CURRENCY_SYMBOLS

        request_url = self.API_BASE + self.API_ENDPOINT_TRANSACTIONS + "fiat"
        params = (
            kwargs
            if kwargs
            else {
                "balanceTypes": balance_types,
                "currencySymbols": currency_symbols,
                "startDate": start_date,
                "endDate": end_date,
            }
        )

        self._update_session_headers()
        history = self._get(request_url, params)
        return history

    @authentication_required
    def get_open_orders(self, pair=None, **kwargs):
        """ Get's list of user's open orders for given pair

        If you specify kwargs, the other parameters will be **overridden**.
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        pair : str, optional
            if not set returns all pairs open orders

        kwargs

        Returns
        -------
        dict
            Data dictionary

            Example of Response Format

            .. code-block:: python

                {
                  'id': '<Order id>',
                  'price': '<Price of the order>',
                  'amount': '<Quantity of the order>',
                  'pairsymbol': '<Pair of the order>',
                  'pairSymbolNormalized': '<Pair of the order with "_" in between.>',
                  'type': '<Type of order. Buy or Sell>',
                  'method': '<Method of order. Limit, Stop Limit..>',
                  'orderClientId': <Order client id created with>,
                  'time': '<Unix time the order was inserted at>',
                  'updateTime': '<Unix time last updated>',
                  'status': <Status of the order. Untouched, Partial>
                },
        """

        request_url = self._create_auth_endpoint_url("openOrders")
        params = kwargs if kwargs else {"pairSymbol": pair}

        self._update_session_headers()
        orders = self._get(request_url, params)
        return orders

    @authentication_required
    def get_all_orders(
        self,
        order_id: int = 0,
        pair_symbol=None,
        start_date=None,
        end_date=None,
        page=None,
        limit=100,
        **kwargs,
    ):

        """ Get's users all orders for given pair

        If you specify kwargs, the other parameters will be **overridden**.
        Only keyword arguments you specified will be used to construct a query.


        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        If start_date not specified, it will get orders for last 30 days.

        Parameters
        ----------
        order_id: int, optional
            If orderId set, it will return all orders greater than or equals to this order id

        pair_symbol: str, mandatory
            Like BTC_TRY, XRP_USDT..

        start_date: int, optional
            start date as timestamp in milliseconds

        end_date: int, optional
            end date as timestamp in milliseconds

        page: int, optional
            page number

        limit: int, optional
            limit number

        kwargs

        Returns
        -------
        list
            List of data dictionaries

            Example Of Response Format

            .. code-block:: python

                [
                  {
                    'id': '<Order id>',
                    'price': '<Price of the order>',
                    'amount': '<Amount of the order>',
                    'quantity': '<Quantity of the order>',
                    'pairsymbol': '<Pair of the order>',
                    'pairSymbolNormalized': '<Pair of the order with "_" in between>',
                    'type': '<Type of order. Buy or Sell>',
                    'method': '<Method of order. Limit, Stop Limit..>',
                    'orderClientId': '<Order client id created with>',
                    'time': '<Unix time the order was inserted at>',
                    'updateTime': '<Unix time last updated>',
                    'status': '<Status of the order. Untouched, Partial..>',

                  },
                  ...
                ]
        """
        request_url = self._create_auth_endpoint_url("allOrders")

        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(
                dt.datetime.today() - dt.timedelta(days=30)
            )
            start_date = int(last_30_days_timestamp * 1000)

        if not end_date:
            end_date = int(time.time() * 1000)

        order_id = order_id - 1 if order_id > 0 else 0

        payload = {
            "orderId": order_id,
            "pairSymbol": pair_symbol,
            "startDate": start_date,
            "endDate": end_date,
            "page": page,
            "limit": limit,
        }
        params = kwargs if kwargs else payload

        self._update_session_headers()
        orders = self._get(request_url, params)
        return orders

    # AUTHENTICATION REQUIRED ORDER IMPLEMENTATIONS
    @authentication_required
    def cancel_order(self, order_id=None):
        """ Deletes The Order

        Parameters
        ----------
        order_id : int, mandatory
        
        Returns
        -------
        bool
            Success value if there is no exception raised by handler
        """
        request_url = self._create_auth_endpoint_url("order")
        params = {"id": order_id}

        self._update_session_headers()
        return self._delete(request_url, params)

    @authentication_required
    def submit_market_order(
        self, quantity=0.0, order_type=None, pair_symbol=None, new_order_client_id=None
    ):
        """ Submits an order in type of 'market order'

        Parameters
        ----------
        quantity : float, mandatory
            Mandatory for market or limit orders.

        order_type : str, mandatory
            'buy' or 'sell'

        pair_symbol : str, mandatory

        new_order_client_id : str, optional

        Returns
        -------
        dict
            Dictionary of order information

            Example of Response Format

            .. code-block:: python

                {
                  'id': '<order id>',
                  'datetime': '<timestamp>',
                  'type': '<Buy or sell>',
                  'method': '<method of order (limit,stop,market)>',
                  'price': '<price>',
                  'stopPrice': '<stop price>',
                  'quantity': '<quantity>',
                  'pairSymbol': '<pair symbol>',
                  'pairSymbolNormalized': '<normalized pair symbol>',
                  'newOrderClientId': '<guid>',
                },

        Raises
        -------
        ValueError
            If wrong pair_symbol entered or file cache for scales hasn't been updated
        """
        if not new_order_client_id:
            new_order_client_id = str(uuid.uuid1())

        amount_scale = self.scale_limits[pair_symbol.upper()]["amount_scale"]
        has_fraction = self.scale_limits[pair_symbol.upper()]["has_fraction"]
        price_scale = (
            self.scale_limits[pair_symbol.upper()]["price_scale"] if has_fraction else 0
        )

        scale = amount_scale if order_type.lower() == "sell" else price_scale

        formatted_qty = str(self._format_unit(unit=quantity, scale=scale))

        params = {
            "quantity": formatted_qty,
            "newOrderClientId": new_order_client_id,
            "orderMethod": "market",
            "orderType": order_type,
            "pairSymbol": pair_symbol,
        }

        return self._submit_order(params)

    @authentication_required
    def submit_limit_order(
        self,
        quantity=0.0,
        price=0.0,
        order_type=None,
        pair_symbol=None,
        new_order_client_id=None,
    ):
        """ Submits an order in type of 'limit order'

        Parameters
        ----------
        quantity : float, mandatory
            Mandatory for market or limit orders.

        price : float, mandatory
            Price field will be ignored for market orders.

        order_type : str, mandatory
            'buy' or 'sell'

        pair_symbol : str, mandatory
            Like 'BTC_TRY', 'XRP_USDT'..

        new_order_client_id : str, optional

        Returns
        -------
        dict
            Dictionary of order information

            Example of Response Format

            .. code-block:: python

                {
                  'id': '<order id>',
                  'datetime': '<timestamp>',
                  'type': '<Buy or sell>',
                  'method': '<method of order (limit,stop,market)>',
                  'price': '<price>',
                  'stopPrice': '<stop price>',
                  'quantity': '<quantity>',
                  'pairSymbol': '<pair symbol>',
                  'pairSymbolNormalized': '<normalized pair symbol>',
                  'newOrderClientId': '<guid>',
                },

        Raises
        -------
        ValueError
            If wrong pair_symbol entered
        """

        if not new_order_client_id:
            new_order_client_id = str(uuid.uuid1())

        scale = self.scale_limits[pair_symbol.upper()]
        amount_scale, price_scale = scale["amount_scale"], scale["price_scale"]
        has_fraction = self.scale_limits[pair_symbol.upper()]["has_fraction"]

        price_scale = price_scale if has_fraction else 0

        formatted_qty = str(self._format_unit(unit=quantity, scale=amount_scale))
        formatted_price = str(self._format_unit(unit=price, scale=price_scale))

        params = {
            "quantity": formatted_qty,
            "price": formatted_price,
            "newOrderClientId": new_order_client_id,
            "orderMethod": "limit",
            "orderType": order_type,
            "pairSymbol": pair_symbol,
        }

        return self._submit_order(params)

    @authentication_required
    def submit_stop_order(
        self,
        stop_price=0.0,
        quantity=0.0,
        price=0.0,
        order_type=None,
        order_method=None,
        pair_symbol=None,
        new_order_client_id=None,
    ):
        """ Submits an order in type of 'stop order'

        Parameters
        ----------
        stop_price: float, mandatory
            For stop orders

        quantity : float, mandatory
            Mandatory for market or limit orders.

        price : float, mandatory
            Price field will be ignored for market orders.

        order_type : str, mandatory
            'buy' or 'sell'

        order_method: str, mandatory
            Either 'stopLimit' or 'stopMarket'

        pair_symbol : str, mandatory

        new_order_client_id : str, optional

        Returns
        -------
        dict
            Dictionary of order information

             Example of Response Format

            .. code-block:: python

                {
                  'id': '<order id>',
                  'datetime': '<timestamp>',
                  'type': '<Buy or sell>',
                  'method': '<method of order (limit,stop,market)>',
                  'price': '<price>',
                  'stopPrice': '<stop price>',
                  'quantity': '<quantity>',
                  'pairSymbol': '<pair symbol>',
                  'pairSymbolNormalized': '<normalized pair symbol>',
                  'newOrderClientId': '<guid>',
                },

        Raises
        ------
        ValueError
            If wrong pair_symbol entered
        """

        if not new_order_client_id:
            new_order_client_id = str(uuid.uuid1())

        scale = self.scale_limits[pair_symbol.upper()]
        amount_scale, price_scale = scale["amount_scale"], scale["price_scale"]

        has_fraction = self.scale_limits[pair_symbol.upper()]["has_fraction"]
        price_scale = price_scale if has_fraction else 0

        formatted_qty = str(self._format_unit(unit=quantity, scale=amount_scale))
        formatted_price = str(self._format_unit(unit=price, scale=price_scale))
        formatted_stop_price = str(self._format_unit(unit=stop_price, scale=price_scale))

        params = {
            "quantity": formatted_qty,
            "price": formatted_price,
            "stopPrice": formatted_stop_price,
            "newOrderClientId": new_order_client_id,
            "orderMethod": order_method,
            "orderType": order_type,
            "pairSymbol": pair_symbol,
        }
        return self._submit_order(params)

    @authentication_required
    def _submit_order(self, params=None, **kwargs):
        """ Submits order for either keyword arguments, or parameter dictionary

        Parameters
        ----------
        params : dict
            dictionary of request parameters

        kwargs

        Returns
        -------
        dict

            Dictionary of order information

            Example of Response Format

            .. code-block:: python

                {
                  'id': '<order id>',
                  'datetime': '<timestamp>',
                  'type': '<Buy or sell>',
                  'method': '<method of order (limit,stop,market)>',
                  'price': '<price>',
                  'stopPrice': '<stop price>',
                  'quantity': '<quantity>',
                  'pairSymbol': '<pair symbol>',
                  'pairSymbolNormalized': '<normalized pair symbol>',
                  'newOrderClientId': '<guid>',
                },
        """

        request_url = self._create_auth_endpoint_url("order")
        self._update_session_headers()

        if kwargs:
            return self._post(request_url, kwargs)
        return self._post(request_url, params)
