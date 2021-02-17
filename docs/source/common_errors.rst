Common Errors & Solutions
=========================

In this section, you will find common errors that you may encounter while using the client.

BTCTurkAuthenticationError
**************************
One of the most common errors that you may encounter is BTCTurkAuthenticationError which means Server has unable to
recognize your identity. Thus, you can't authenticate.

Wrong API Credentials
---------------------
- When you are creating your key/secret pair, you provide your machine's public IPv4 address. Make sure that you are providing
  the correct address. In addition to that, if you are using this client on a Virtual Machine, you must get credentials for
  that machine's public IPv4 address, always keep that in mind.

- When you are doing copy/paste, you may miss some characters, always check when you paste your credentials.

- Make sure you have authorized your credentials with correct permissions (buy-sell / see balance etc.)

Invalid Nonce
-------------
In order to authenticate, your machine's time and Btcturk Server's time must match. If it doesn't, you will get an
authentication error with Invalid Nonce message. Again, if you are using a virtual machine, make sure these times match.

You can check Btcturk's server time by creating a client without key/secret pair and calling `client.get_server_time()`
method.
