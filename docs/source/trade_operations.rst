Trade Operations
================

Important Note About Orders
***************************
We are going to talk about concepts like quantity, price in next subsections of this chapter.

Users usually misinterpret those concepts and get various scaling errors, let's dive in these concepts one by one.

Numerator / Denominator
-----------------------
These concepts will be used to explain trades in a more clear way. In a trade pair such as **BTC/USDT**,
first one is Numerator, second one is Denominator. In this example Numerator is **BTC**, Denominator is **USDT**.

Quantity
--------
In market orders, since price is determined by current market value you only provide a **quantity parameter** for your trade.

If you are **buying**, denominator will be used as quantity unit, but if you are selling numerator becomes the quantity.

If you are confused with these terms, don't worry! Here's a few cases which includes might want to sell or buy bitcoin.
After looking these cases, you will understand why people misinterprets the concept quantity and what actually means.

**Quick Example**

I want to trade Bitcoin with USDT.

**Case 1:**

I want to buy bitcoin.

**Wrong Approach**:

I want to buy 0.05 bitcoin, so this is my quantity. I can call submit market order method with 'quantity=0.05'

**WRONG!** This is misinterpreted by beginner client users all the time.

If you provide 0.05 as quantity for BTC/USDT pair, **you tell the api that you want to buy bitcoin for worth of 0.05 USDT**,
you will get either min_total_value error or scaling error if you do that.

Don't forget, since you are buying, denominator in this pair should be your quantity. Thus, USDT!

**Correct Approach:**

I'm going to buy Bitcoin with my USDT with market price, i want to trade my 100 USDT with bitcoin, so my quantity is 100.

**Case 2:**

I want to sell bitcoin.

Selling should not be confusing. In BTC/USDT pair, if you want to sell 0.05 Bitcoin, your quantity is 0.05. Pretty
straightforward

Price
-----
Price is pretty straightforward too. It is the value of cryptocurrency in stock exchange.

You can only use price parameter with stop orders and limit orders.


Submit Market Order / Code Examples
***********************************

**Usage Example 1:**

- Pair: XRP/USDT
- Goal: Buying XRP for 100 USDT

.. code-block:: python

    >>> my_client.submit_market_order(
          quantity=100.0,
          order_type='buy',
          pair_symbol='XRP_USDT'
        )

**Usage Example 2:**

- Pair: ETH/TRY
- Goal: Selling 1250 ETH exchange of TRY


.. code-block:: python

    >>> my_client.submit_market_order(
          quantity=1250.0,
          order_type='sell',
          pair_symbol='ETH_TRY'
        )

Submit Limit Order / Code Examples
**********************************
**Usage Example 1:**

- Pair: XRP/USDT
- Goal: Place a Limit Buy Order for 400 XRP with price of 0.16 USDT

.. code-block:: python

    >>> my_client.submit_limit_order(
          quantity=400.0,
          price=0.16,
          order_type='buy',
          pair_symbol='XRP_USDT'
        )

**Usage Example 2:**

- Pair: ETH/TRY
- Goal: Place a Limit Sell Order for 1250 ETH with price of 1950 USDT

.. code-block:: python

    >>> my_client.submit_limit_order(
          quantity=1250.0,
          price=1950,
          order_type='sell',
          pair_symbol='ETH_USDT'
        )

Submit Stop Limit Order / Code Examples
***************************************
**Usage Example 1:**

- Pair: BTC/USDT
- Goal: If Bitcoin price hits 50.000 USDT, we're going to place a limit buy order with quantity=0.05 and price=50.500

.. code-block:: python

    >>> my_client.submit_limit_order(
          quantity=0.05,
          price=50500,
          stop_price=50000
          order_type='buy',
          pair_symbol='BTC_USDT'
        )

**Usage Example 2:**

- Pair: BTC/USDT
- Goal: If Bitcoin price drops 40.000 USDT, we're going to place a limit sell order with quantity=0.05 and price=39.500

.. code-block:: python

    >>> my_client.submit_limit_order(
          quantity=0.05,
          price=39500,
          stop_price=40000
          order_type='sell',
          pair_symbol='BTC_USDT'
        )
