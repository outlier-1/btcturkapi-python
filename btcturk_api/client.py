from btcturk_api.properties import authentication_required
from btcturk_api.exceptions import BadRequestError, InternalServerError, InvalidRequestParameterError, \
    BTCTurkAuthenticationError
from btcturk_api.constants import CRYPTO_SYMBOLS, CURRENCY_SYMBOLS, DEPOSIT_OR_WITHDRAWAL, TRADE_TYPES, SCALE_LIMITS
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
        """ Creates a Client Object with given API Keys

        Initializes a requests.Session object for connection that will be used.
        If user specifies both api_key and secret_key, constructor will try to authenticate the user
        by updating session headers and sending a request to btcturk api with given credential information.

        Parameters
        ----------
        api_key : str, optional
        api_secret: str, optional
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.authenticated = False
        self.session = self._init_session()

        if api_key and api_secret:
            self.authenticate()

    @staticmethod
    def _init_session():
        """ Initializes a requests.Session object with headers

        Returns
        -------
        requests.Session
            Session instance with some headers
        """
        session = requests.session()
        headers = {
            "Content-Type": "application/json"
        }
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
            url with format https://api.btcturk.com/api/v2/endpoint
        """
        return f"{self.API_BASE}{self.API_ENDPOINT_NON_AUTH}{endpoint}"

    def _create_auth_endpoint_url(self, endpoint):
        """ Constructs Auth Required Endpoint Url

        Parameters
        ----------
        endpoint : str, optional

        Returns
        -------
        str
            url with format https://api.btcturk.com/api/v1/endpoint
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
        data = "{}{}".format(self.api_key, stamp).encode('utf-8')
        signature = hmac.new(api_secret, data, hashlib.sha256).digest()
        signature = base64.b64encode(signature)
        return signature

    def _update_session_headers(self, **kwargs):
        """ Updates Client's session's headers

        This is important because before each call to authentication required endpoints,
        HMAC-SHA256 message, which is time dependent, should be in headers for authorization.

        Parameters
        ----------
        kwargs : kwargs
            any key, value that will be added to header

        """
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

        """
        url = self._create_auth_endpoint_url('users/balances')
        signature = self._create_signature()
        headers = {
            "X-PCK": self.api_key,
            "X-Stamp": str(int(time.time()) * 1000),
            "X-Signature": str(signature.decode('utf-8')),
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
        self._handle_response(response)  # TODO: Need to raise exception (like _post), if error occurs
        return response.json()['data']

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

        if not response.json()['success']:
            raise InvalidRequestParameterError(response)

        return response.json()['data']

    def _delete(self, url, params=None):
        """ Wrapper for HTTP Delete Method

        Parameters
        ----------
        url : str, mandatory
            Destination URL

        params : dict, optional
            request parameters

        Returns
        -------
        bool
            Success value if there is no exception raised by handler
        """
        response = self.session.delete(url=url, params=params, data=json.dumps(params))
        self._handle_response(response)

        return response.json()['success']

    # PUBLIC ENDPOINT IMPLEMENTATIONS

    def get_exchange_info(self, symbol_list=None):
        """ Price Ticker

        Method for getting exchange info of any given pair

        Parameters
        ----------
        symbol_list : List of Symbols in format ['BTCUSDT', 'XRPUSDT', 'ETHTRY' ...], optional
            pair symbols must be in format Pair1Pair2, not Pair1_Pair2

        Returns
        -------
        list
            a list of data dictionaries of all pairs if symbol_list is not set
            or list of exchange information in symbol list
        """

        request_url = self._create_public_endpoint_url('server/exchangeinfo')
        exchange_list = self._get(request_url)['symbols']

        if not symbol_list:
            return exchange_list

        filtered_list = list(filter(lambda u: u['name'] in symbol_list, exchange_list))
        return filtered_list

    def get_server_time(self, as_timestamp=False):
        """ Gets Current Server Time

        Method for getting server time info, both unix timestamp and DATE:TIME format.

        Parameters
        ----------
        as_timestamp : bool, optional
            if true, directly returns the unix-timestamp integer instead of server response.

        Returns
        -------
        if as_timestamp:
            int
                Unix-timestamp
        else:
            dictionary
                if request is successful, returns a dictionary object with 2 keys
                'serverTime': Unix Timestamp as 'int' object
                'serverTime2': Datetime string

                Result Dictionary Has These Keys:

                pairSymbol: Requested pair symbol
                pairSymbolNormalized: Requested pair symbol with "_" in between.
        """
        request_url = self._create_public_endpoint_url('server/time')
        response = self.session.get(url=request_url)
        self._handle_response(response)
        response_as_json = response.json()

        if as_timestamp:
            return response_as_json['serverTime']

        return response_as_json

    def tick(self, pair=None, **kwargs):
        """ Price Ticker

        Method for getting price related information of any given pair

        !!! IMPORTANT !!!
        If you specify kwargs, the other parameters will be overridden.
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        pair : PAIR_SYMBOLS, mandatory
            pair symbol like 'BTC_TRY', 'ETH_BTC', ... all possible symbols are in PAIR_SYMBOLS Tuple

        kwargs

        Returns
        -------
        list
            a list of data dictionaries of all pairs if pair is not set
            or one element list which contains the data dictionary of pair.

            Data Dictionary Has These Keys:

            pairSymbol: Requested pair symbol
            pairSymbolNormalized: Requested pair symbol with "_" in between.
            timestamp: Current Unix time in milliseconds
            last: Last price
            high: Highest trade price in last 24 hours
            low: Lowest trade price in last 24 hours
            bid: Highest current bid
            ask: Lowest current ask
            open: Price of the opening trade in last 24 hours
            volume: Total volume in last 24 hours
            average: Average Price in last 24 hours
            daily: Price change in last 24 hours
            dailyPercent: Price change percent in last 24 hours
            denominatorSymbol: Denominator currency symbol of the pair
            numeratorSymbol: Numerator currency symbol of the pair
        """
        request_url = self._create_public_endpoint_url('ticker')
        params = kwargs if kwargs else {}

        if pair:
            return self._get(request_url, {'pairSymbol': pair})
        return self._get(request_url, params)

    def get_order_book(self, pair=None, limit=100, **kwargs):
        """ Gets the order book of given pair

        !!! IMPORTANT !!!
        If you specify kwargs, the other parameters will be overridden.
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        pair : PAIR_SYMBOLS, mandatory
            pair symbol like 'BTC_TRY', 'ETH_BTC', ... all possible symbols are in PAIR_SYMBOLS Tuple

        limit : int, optional
            default 100 max 1000

        kwargs

        Returns
        -------
        dict
            data dictionary

            Data Dictionary Has These Keys:

            timestamp: Current Unix time in milliseconds
            bids: Array of current open bids on the orderbook.
            asks: Array of current open asks on the orderbook.

        """
        request_url = self._create_public_endpoint_url('orderbook')
        params = kwargs if kwargs else {'pairSymbol': pair, 'limit': limit}

        return self._get(request_url, params)

    def get_trades(self, pair=None, last=50, **kwargs):
        """ Gets a list of Trades for given pair

        !!! IMPORTANT !!!
        If you specify kwargs, the other parameters will be overridden.
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        pair : PAIR_SYMBOLS, mandatory
            pair symbol like 'BTC_TRY', 'ETH_BTC', ... all possible symbols are in PAIR_SYMBOLS Tuple

        last : int, optional
            default 50 max 1000

        Returns
        -------
        dict
            data dictionary

            Data Dictionary Has These Keys:

            pair: Requested pair symbol
            pairNormalized: Request Pair symbol with "_" in between.
            numerator: Numerator currency for the requested pair
            denominator: Denominator currency for the requested pair
            date: Unix time of the trade in milliseconds
            tid: Trade ID
            price: Price of the trade
            amount: Amount of the trade
        """
        request_url = self._create_public_endpoint_url('trades')
        params = kwargs if kwargs else {'pairSymbol': pair, 'last': last}

        return self._get(request_url, params=params)

    # AUTHENTICATION REQUIRED GET ENDPOINT IMPLEMENTATIONS

    @authentication_required
    def get_account_balance(self):
        """ Gets the list of balances that user have

        Returns
        -------
        list
            list of balance dictionaries,

            Each Balance Dictionary Has These Keys:

            asset: Asset symbol
            assetname: Asset name
            balance: Total asset balance including open orders and pending withdrawal requests
            locked: Asset locked amount in open orders and withdrawal requests
            free: Asset available amount for trading

        """
        url = self._create_auth_endpoint_url('users/balances')
        self._update_session_headers()
        balance_list = self._get(url)
        return balance_list

    @authentication_required
    def get_trade_history(self, trade_type=None, symbol=None,
                          start_date=None, end_date=None, **kwargs):
        """ Gets the history of user's trades.

        If start_date not specified, it will get trades for last 30 days.
        If trade_type not specified, both 'buy' and 'sell' types will be used
        If symbol not specified, all crypto symbols will be used

        !!! IMPORTANT !!!
        If you specify kwargs, the other parameters will be overridden.
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        trade_type : list -> str ["buy", "sell"], optional

        symbol : list -> str ["btc", "try", ...etc.], optional

        start_date : timestamp, optional

        end_date : timestamp, optional

        kwargs

        Returns
        -------
        list
            List of trade data dictionaries,

            Each Data Dictionary Has These Keys:

            price: Trade price
            numeratorSymbol: Trade pair numerator symbol
            denominatorSymbol: Trade pair denominator symbol
            orderType: Trade type (buy,sell)
            id: Trade id
            timestamp: Unix timestamp
            amount: Trade Amount (always negative if order type is sell)
            fee: Trade fee
            tax: Trade tax

        """
        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(dt.datetime.today() - dt.timedelta(days=30))
            start_date = int(last_30_days_timestamp * 1000)

        if not end_date:
            end_date = int(time.time() * 1000)

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
    def get_crypto_history(self, symbol=None, _type=None, start_date=None, end_date=None, **kwargs):
        """ Gets the history of user's crypto transactions.

        If start_date not specified, it will get trades for last 30 days.
        If _type not specified, both 'withdrawal' and 'deposit' types will be used
        If symbol not specified, all crypto symbols will be used

        !!! IMPORTANT !!!
        If you specify kwargs, the other parameters will be overridden.
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        _type : list -> str ["deposit", "withdrawal"], optional

        symbol : list -> str ["btc", "try", ...etc.], optional

        start_date : timestamp, optional

        end_date : timestamp, optional

        kwargs

        Returns
        -------
        list
            List of trade data dictionaries,

            Each Data Dictionary Has These Keys:

            balanceType: Type of transaction (deposit, withdrawal)
            currencySymbol: Transaction currency symbol
            id: Transaction id
            timestamp: Unix timestamp
            funds: Funds
            amount: Transaction Amount
            fee: Transaction fee
            tax: Transaction tax
        """
        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(dt.datetime.today() - dt.timedelta(days=30))
            start_date = int(last_30_days_timestamp * 1000)

        if not end_date:
            end_date = int(time.time() * 1000)

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
                         start_date=None, end_date=None, **kwargs):
        """ Gets the history of user's fiat transactions.

        If start_date not specified, it will get trades for last 30 days.
        If balance_types not specified, both 'withdrawal' and 'deposit' types will be used
        If currency_symbols not specified, all currency symbols will be used

        !!! IMPORTANT !!!
        If you specify kwargs, the other parameters will be overridden.
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        Parameters
        ----------
        balance_types : list -> str ["buy", "sell"], optional

        currency_symbols : list -> str ["try", ...etc.], optional

        start_date : timestamp, optional

        end_date : timestamp, optional

        kwargs

        Returns
        -------
        list
            List of trade data dictionaries,

            Each Data Dictionary Has These Keys:

            balanceType: Type of transaction (deposit, withdrawal)
            currencySymbol: Transaction currency symbol
            id: Transaction id
            timestamp: Unix timestamp
            funds: Funds
            amount: Transaction Amount
            fee: Transaction fee
            tax: Transaction tax

        """
        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(dt.datetime.today() - dt.timedelta(days=30))
            start_date = int(last_30_days_timestamp * 1000)

        if not end_date:
            end_date = int(time.time() * 1000)

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
        """ Get's list of user's open orders for given pair

        !!! IMPORTANT !!!
        If you specify kwargs, the other parameters will be overridden.
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

                Each Data Dictionary Has These Keys:

                id: Order id
                price: Price of the order
                amount: Amount of the order
                quantity: quantity of the order
                pairsymbol: Pair of the order
                pairSymbolNormalized: Pair of the order with "_" in between.
                type: Type of order. Buy or Sell
                method: Method of order. Limit, Stop Limit
                orderClientId: Order client id created with (GUID if not set by user)
                time: Unix time the order was inserted at
                updateTime: Unix time last updated
                status: Status of the order. Untouched (not matched), Partial (matched partially)

        """
        request_url = self._create_auth_endpoint_url('openOrders')
        params = kwargs if kwargs else {'pairSymbol': pair}

        self._update_session_headers()
        orders = self._get(request_url, params)
        return orders

    @authentication_required
    def get_all_orders(self, order_id=0, pair_symbol=None, start_date=None,
                       end_date=None, page=None, limit=100, **kwargs):

        """ Get's users all orders for given pair

        !!! IMPORTANT !!!
        If you specify kwargs, the other parameters will be overridden.
        Only keyword arguments you specified will be used to construct a query.
        Therefore, it is your choice to use kwargs.

        But i strongly discourage you to use that for avoiding any invalid requests

        If start_date not specified, it will get orders for last 30 days.

        Parameters
        ----------
        order_id: int, optional
            If orderId set, it will return all orders greater than or equals to this order id

        pair_symbol: str, mandatory
            pair symbol

        start_date: int, optional
            start date as timestamp

        end_date: int, optional
            end date as timestamp

        page: int, optional
            page number

        limit: int, optional
            limit number

        kwargs

        Returns
        -------
        list
            List of data dictionaries

                Each Data Dictionary Has These Keys:

                id: Order id
                price: Price of the order
                amount: Amount of the order
                quantity: quantity of the order
                pairsymbol: Pair of the order
                pairSymbolNormalized: Pair of the order with "_" in between.
                type: Type of order. Buy or Sell
                method: Method of order. Limit, Stop Limit
                orderClientId: Order client id created with (GUID if not set by user)
                time: Unix time the order was inserted at
                updateTime: Unix time last updated
                status: Status of the order. Untouched (not matched), Partial (matched partially)
        """
        request_url = self._create_auth_endpoint_url('allOrders')

        if not start_date:
            last_30_days_timestamp = dt.datetime.timestamp(dt.datetime.today() - dt.timedelta(days=30))
            start_date = int(last_30_days_timestamp * 1000)

        if not end_date:
            end_date = int(time.time() * 1000)

        order_id = order_id - 1 if order_id > 0 else 0

        payload = {
            'orderId': order_id,
            'pairSymbol': pair_symbol,
            'startDate': start_date,
            'endDate': end_date,
            'page': page,
            'limit': limit
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
        request_url = self._create_auth_endpoint_url('order')
        params = {'id': order_id}

        self._update_session_headers()
        return self._delete(request_url, params)

    @authentication_required
    def submit_market_order(self, quantity=0.0, order_type=None,
                            pair_symbol=None, new_order_client_id=None):
        """ Submits an order in type of 'market order'

        Parameters
        ----------
        quantity : decimal, mandatory
            Mandatory for market or limit orders.

        order_type : str, mandatory
            'buy' or 'sell'

        pair_symbol : str, mandatory

        new_order_client_id : str, optional

        Returns
        -------
        dict
            Dictionary of order information

            Data Dictionary has these fields:
            id: order id,
            datetime: timestamp,
            type: Buy or sell,
            method: method of order (limit,stop,market),
            price: price,
            stopPrice: stop price,
            quantity: quantity,
            pairSymbol": pair symbol,
            pairSymbolNormalized: "normalized pair symbol",
            newOrderClientId: guid
        """
        if not new_order_client_id:
            new_order_client_id = str(uuid.uuid1())

        amount_scale = SCALE_LIMITS[pair_symbol.upper()]['amount_scale']
        formatted_qty = "{quantity:.{amount_scale}f}".format(quantity=quantity, amount_scale=amount_scale)

        params = {'quantity': formatted_qty, 'newOrderClientId': new_order_client_id, 'orderMethod': 'market',
                  'orderType': order_type, 'pairSymbol': pair_symbol}

        return self.submit_order(params)

    @authentication_required
    def submit_limit_order(self, quantity=0.0, price=0.0, order_type=None,
                           pair_symbol=None, new_order_client_id=None):
        """ Submits an order in type of 'limit order'


        Parameters
        ----------
        quantity : decimal, mandatory
            Mandatory for market or limit orders.

        price : decimal, mandatory
            Price field will be ignored for market orders. Market orders get filled with different prices until
            your order is completely filled. There is a 5% limit on the difference between the first price and the last
            price. İ.e. you can't buy at a price more than 5% higher than the best sell at the time of order submission
            and you can't sell at a price less than 5% lower than the best buy at the time of order submission

        order_type : str, mandatory
            'buy' or 'sell'

        pair_symbol : str, mandatory

        new_order_client_id : str, optional

        Returns
        -------
        dict
            Dictionary of order information

            Data Dictionary has these fields:
            id: order id,
            datetime: timestamp,
            type: Buy or sell,
            method: method of order (limit,stop,market),
            price: price,
            stopPrice: stop price,
            quantity: quantity,
            pairSymbol": pair symbol,
            pairSymbolNormalized: "normalized pair symbol",
            newOrderClientId: guid
        """
        if not new_order_client_id:
            new_order_client_id = str(uuid.uuid1())

        scale = SCALE_LIMITS[pair_symbol.upper()]
        amount_scale, price_scale = scale['amount_scale'], scale['price_scale']

        formatted_qty = "{quantity:.{amount_scale}f}".format(quantity=quantity, amount_scale=amount_scale)
        formatted_price = "{price:.{price_scale}f}".format(price=price, price_scale=price_scale)

        params = {
            'quantity': formatted_qty, 'price': formatted_price, 'newOrderClientId': new_order_client_id,
            'orderMethod': 'limit', 'orderType': order_type, 'pairSymbol': pair_symbol
        }

        return self.submit_order(params)

    @authentication_required
    def submit_stop_order(self, stop_price=0.0, quantity=0.0, price=0.0, order_type=None,
                          pair_symbol=None, new_order_client_id=None):
        """ Submits an order in type of 'stop order'

        Parameters
        ----------
        stop_price: decimal, mandatory
            For stop orders

        quantity : decimal, mandatory
            Mandatory for market or limit orders.

        price : decimal, mandatory
            Price field will be ignored for market orders. Market orders get filled with different prices until
            your order is completely filled. There is a 5% limit on the difference between the first price and the last
            price. İ.e. you can't buy at a price more than 5% higher than the best sell at the time of order submission
            and you can't sell at a price less than 5% lower than the best buy at the time of order submission

        order_type : str, mandatory
            'buy' or 'sell'

        pair_symbol : str, mandatory
        new_order_client_id : str, optional

        Returns
        -------
        dict
            Dictionary of order information

            Data Dictionary has these fields:
            id: order id,
            datetime: timestamp,
            type: Buy or sell,
            method: method of order (limit,stop,market),
            price: price,
            stopPrice: stop price,
            quantity: quantity,
            pairSymbol": pair symbol,
            pairSymbolNormalized: "normalized pair symbol",
            newOrderClientId: guid
        """
        if not new_order_client_id:
            new_order_client_id = str(uuid.uuid1())

        scale = SCALE_LIMITS[pair_symbol.upper()]
        amount_scale, price_scale = scale['amount_scale'], scale['price_scale']

        formatted_qty = "{quantity:.{amount_scale}f}".format(quantity=quantity, amount_scale=amount_scale)
        formatted_price = "{price:.{price_scale}f}".format(price=price, price_scale=price_scale)
        formatted_stop_price = "{price:.{price_scale}f}".format(price=stop_price, price_scale=price_scale)

        params = {
            'quantity': formatted_qty, 'price': formatted_price, 'stopPrice': formatted_stop_price,
            'newOrderClientId': new_order_client_id, 'orderMethod': 'market', 'orderType': order_type,
            'pairSymbol': pair_symbol
        }

        return self.submit_order(params)

    @authentication_required
    def submit_order(self, params=None, **kwargs):
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

            Data Dictionary has these fields:
            id: order id,
            datetime: timestamp,
            type: Buy or sell,
            method: method of order (limit,stop,market),
            price: price,
            stopPrice: stop price,
            quantity: quantity,
            pairSymbol": pair symbol,
            pairSymbolNormalized: "normalized pair symbol",
            newOrderClientId: guid
        """
        request_url = self._create_auth_endpoint_url('order')
        self._update_session_headers()

        if kwargs:
            return self._post(request_url, kwargs)
        return self._post(request_url, params)
