Account Related Endpoints
=========================


Get Account Balance
*******************

You can use this method for accessing your account balance information.

Method returns all balances by default, if you want specific assets, you should give list of assets as 'assets' parameter.

Here's an example, returning BTC and ETH balance information:

.. code-block:: python

    >>> my_client.get_account_balance(assets=['BTC', 'ETH'])
    [
      {
        'asset': 'BTC',
        'assetname': 'Bitcoin',
        'balance': '0.0003670154826363',
        'locked': '0',
        'free': '0.0003670154826363',
        'orderFund': '0',
        'requestFund': '0',
        'precision': 8
      },
      {
        'asset': 'ETH',
        'assetname': 'Ethereum',
        'balance': '0',
        'locked': '0',
        'free': '0',
        'orderFund': '0',
        'requestFund': '0',
        'precision': 8
      }
    ]

If you want to know more about this response and method's usage, check detailed information by clicking here.

Get Trade History
*****************
Usage Scenerio: Users want to access their trade history for last **90** days. But only **buy** trades needed and they want only
bitcoin and ripple trades.

.. code-block:: python

    >>> from datetime import datetime, timedelta
    >>> start_date = (datetime.now() - timedelta(days=90)).timestamp()
    >>> start_date = int(start_date * 1000)  # Timestamp should be in milliseconds
    >>> my_client.get_trade_history(
            trade_type=['buy'],
            symbol=['btc', 'xrp'],
            start_date=start_date
        )

Get Crypto History
******************
Scenerio: Users want to access their trade history for last **90** days. But only **buy** orders needed and they want only
bitcoin and ripple trades.

.. code-block:: python

    >>> from datetime import datetime, timedelta
    >>> start_date = (datetime.now() - timedelta(days=90)).timestamp()
    >>> start_date = int(start_date * 1000)  # Timestamp should be in milliseconds
    >>> my_client.get_trade_history(
            trade_type=['buy'],
            symbol=['btc', 'xrp'],
            start_date=start_date
        )


Get Fiat History
*****************
Scenerio: Users want to access their trade history for last **90** days. But only **buy** orders needed and they want only
bitcoin and ripple trades.

.. code-block:: python

    >>> from datetime import datetime, timedelta
    >>> start_date = (datetime.now() - timedelta(days=90)).timestamp()
    >>> start_date = int(start_date * 1000)  # Timestamp should be in milliseconds
    >>> my_client.get_trade_history(
            trade_type=['buy'],
            symbol=['btc', 'xrp'],
            start_date=start_date
        )

Get Open Orders
*****************
Usage Scenario: Users want to get information about their open orders for all cryptocurrencies

.. code-block:: python

    >>> my_client.get_open_orders()

Get All Orders
*****************
Usage Scenario: Users want to get their all ripple orders for last **6 hours**:

.. code-block:: python

    >>> from datetime import datetime, timedelta
    >>> start_date = (datetime.now() - timedelta(hours=6)).timestamp()
    >>> start_date = int(start_date * 1000)  # Timestamp should be in milliseconds
    >>> my_client.get_all_orders(
            pair_symbol='XRP_TRY',
            start_date=start_date
        )
