Quickstart
==========
btcturkapi-python is a wrapper library built around Btcturk's REST api implementation.

It provides more abstract version of REST Client for traders using Btcturk as a cryptocurrency platform.


Installation
************

You can install this library via pip.

It is the best practice using a virtual environment for your project, keep that in mind.

Run this command through terminal:

.. code-block:: bash

   $ pip install btcturk-api

Since the project's current version doesn't have support for websockets and any advanced features, dependencies are simple and you should not encounter any installation error.

Usage
*****

After installing the library, just import the client and you are good to go. You can use any feature btcturk api provides without dealing with preparing requests, handling responses etc.

.. code-block:: python

    >>> from btcturk_api.client import Client

You can use public endpoints without providing an api key/secret pair.

.. code-block:: python

    >>> my_client = Client()
    >>> my_client.get_server_time()
    {'serverTime': 1613292018131, 'serverTime2': '2021-02-14T08:40:18.1308832+00:00'}

If you have an api key/secret pair, you can use *account endpoints* and *trading operations*

.. code-block:: python

    >>> my_client = Client(api_key='<Your Api Key>', api_secret='<Your Api Secret>')
    >>> my_client.get_account_balance()
    [
      {
       'asset': 'TRY',
       'assetname': 'Türk Lirası',
       'balance': '0.8462753436459292',
       'locked': '0',
       'free': '0.8462753436459292',
       'orderFund': '0',
       'requestFund': '0',
       'precision': 2
       },
       {...}
    ]

