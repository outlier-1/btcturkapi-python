Public Endpoints
================

Get Server Time
***************

If you are encountering BTCTurkAuthenticationError, reason might be time inconsistency between server and your machine.
You can get server's time with this method:

.. code-block:: python

    >>> my_client.get_server_time()
    {
      'serverTime': 1613313462021,
      'serverTime2': '2021-02-14T14:37:42.0214779+00:00'
    }

Get Exchange Info
*****************

.. code-block:: python

    >>> my_client.get_exchange_info()
    [
      {
        'id': 1,
        'name': 'BTCTRY',
        'nameNormalized': 'BTC_TRY',
        'status': 'TRADING',
        'numerator': 'BTC',
        'denominator': 'TRY',
        'numeratorScale': 8,
        'denominatorScale': 2,
        'hasFraction': False,
        'filters': [{'filterType': 'PRICE_FILTER', 'minPrice': '0.0000000000001', 'maxPrice': '10000000', ....],
        'orderMethods': ['MARKET', 'LIMIT', 'STOP_MARKET', 'STOP_LIMIT'],
        'displayFormat': '#,###',
        'commissionFromNumerator': False,
        'order': 1000,
        'priceRounding': False
      },
      {...}
    ]

Get Ticker
**********

.. code-block:: python

    >>> my_client.tick()
    {
      'pair': 'BTCTRY',
      'pairNormalized': 'BTC_TRY',
      'timestamp': 1613313834273,
      'last': 350000.0,
      'high': 354975.0,
      'low': 332565.0,
      'bid': 350000.0,
      'ask': 350904.0,
      'open': 332775.0,
      'volume': 1718.94206874,
      'average': 344569.69406522,
      'daily': 18129.0,
      'dailyPercent': 5.18,
      'denominatorSymbol': 'TRY',
      'numeratorSymbol': 'BTC',
      'order': 1000
      }


Get Order book
**************

.. code-block:: python

    >>> my_client.get_order_book(pair='BTCTRY', limit=1)
    {'timestamp': 1613315997466.0,
    'bids': [['349600.00', '0.00518551']],
    'asks': [['349830.00', '10.62911645']]
    }

Get Trades
**********

.. code-block:: python

    >>> my_client.get_trades(pair='BTCTRY')
    [
      {
        'pair': 'BTCTRY',
        'pairNormalized': 'BTC_TRY',
        'numerator': 'BTC',
        'denominator': 'TRY',
        'date': 1613316100877,
        'tid': '637489129008759423',
        'price': '349000.00',
        'amount': '0.00500000',
        'side': 'sell'
       },
       {....}
    ]

