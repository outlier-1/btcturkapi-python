Exceptions
==========

InvalidRequestParameterError
****************************
When you provide invalid parameters, you get this exception. For proper usage of parameters, check BTCTurk API section
of this documentation and learn more about the method you want to use.

BTCTurkAuthenticationError
**************************
When server can't authenticate you, this exception will be raised. In Exceptions sections, reasons of that explained.

RequestLimitExceededError
****************************
When you exceed Btcturk's api response limits, this exception will be raised. Check Btcturk's documentation for api limits.

InternalServerError
*******************
Raised for 5xx errors. If response message is html instead of json.