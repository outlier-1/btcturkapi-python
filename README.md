# BTCTurk API - Python Wrapper

btcturkapi-python is a wrapper library built around Btcturk's REST api implementation.

It provides more abstract version of REST Client for traders using Btcturk as a cryptocurrency platform.

## Documentation

Check out the [documentation](https://btcturkapi-python.readthedocs.io/en/latest/) for learning  how to use this library and further reference

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [Features](#features)
* [Quickstart](#Quickstart)
  * [Requirements](#Requirements)
  * [Installation](#Installation)
* [Usage](#Usage)
* [License](#License)
* [Contact](#contact)
* [Donation](#Donation)



<!-- Features -->
## Features

* Monitor cryptocurrency prices.
* Place buy, sell orders with stop, limit, or market methods.
* List and cancel open orders.
* Get crypto/fiat transaction history.


<!-- GETTING STARTED -->
## Quickstart

In order to use this library for your projects, you can checkout installation and usage sections

### Requirements
 
* BTCTurk API Credentials (For Authentication Necessary Operations)
```
https://www.btcturk.com/ApiAccess
```
You can go to link above and create your api credentials.


### Installation

You can install this library via pip.

It is the best practice using a virtual environment for your project, keep that in mind.

Run this command through terminal:

```sh
pip install btcturk-api 
```
Since the project's current version doesn't have support for websockets and any advanced features, dependencies are simple and you should not encounter any installation error.

<!-- USAGE EXAMPLES -->
## Usage

After installing the library, just import the client and you are good to go. You can use any feature btcturk api provides without dealing with preparing requests, handling responses etc.

```py
from btcturk_api.client import Client
```
You can use public endpoints without providing an api key/secret pair.

```py
>>> my_client = Client()
    >>> my_client.get_server_time()
    {'serverTime': 1613292018131, 'serverTime2': '2021-02-14T08:40:18.1308832+00:00'}
```
If you have an api key/secret pair, you can use account endpoints and trading operations

```py
>>> my_client = Client(api_key='<Your Api Key>', api_secret='<Your Api Secret>')
>>> my_client.get_account_balance()
    [
      {
       'asset': 'TRY',
       'assetname': 'Türk Lirası',
       'balance': '100.00',
       'locked': '0',
       'free': '100.00',
       'orderFund': '0',
       'requestFund': '0',
       'precision': 2
       },
       {...}
    ]
```
<!-- LICENSE -->
## License

You can use this library in your personal projects free of charge. Detailed information is in LICENSE.txt file.

<!-- CONTACT -->
## Contact

Miraç Baydemir -  omermirac59@gmail.com

Project Link: [https://github.com/outlier-1/btcturkapi-python/](https://github.com/outlier-1/btcturkapi-python/)

<!-- DONATION -->
## Donation

Bitcoin Address - '34FSjtdwTSB21uVDcptgJ8kPHHimMSCGxq'

