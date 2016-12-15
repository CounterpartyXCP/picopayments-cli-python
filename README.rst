###################
PicoPayments Client
###################

|BuildLink|_ |CoverageLink|_ |LicenseLink|_ |IssuesLink|_


.. |BuildLink| image:: https://travis-ci.org/StorjRND/picopayments-client-python.svg
.. _BuildLink: https://travis-ci.org/StorjRND/picopayments-client-python

.. |CoverageLink| image:: https://coveralls.io/repos/StorjRND/picopayments-client-python/badge.svg
.. _CoverageLink: https://coveralls.io/r/StorjRND/picopayments-client-python

.. |LicenseLink| image:: https://img.shields.io/badge/license-MIT-blue.svg
.. _LicenseLink: https://raw.githubusercontent.com/F483/picopayments-client-python/master/LICENSE

.. |IssuesLink| image:: https://img.shields.io/github/issues/F483/picopayments-client-python.svg
.. _IssuesLink: https://github.com/F483/picopayments-client-python/issues


Micropayment hub client for counterparty assets.

API Calls
#########

version
=======

Returns current version of number.


hubstatus
=========

Get current hub status.

Arguments
---------

 * asset (str): Optionally limit output to given asset.

Returns
-------

.. code::

    List of open connections, current terms, funding addresses
    and current liquidity for new connections.

    {
      "connections": {
        "a0b1156206dedb1aa24084752b5693a9022349dc547fb9952aa510003e93": {
          "asset": "XCP",
          "balance": 31338,
          "status": "open",
          "ttl": 401
        }
      },
      "current_terms": {
        "XCP": {
          "deposit_max": 0,
          "deposit_min": 0,
          "deposit_ratio": 1.0,
          "expire_max": 0,
          "expire_min": 0,
          "sync_fee": 1
        }
      },
      "funding_addresses": {
        "BTC": "mhzPMMC3hkQUL9HUYY13s2NehEJXCA923Z",
        "XCP": "n1f73Cvxi7KFWK5p7W8F6JYbyQxV5djqUo"
      },
      "liquidity": {
        "addresses": {
          "XCP": [
            {
              "address": "mzEPqJet1LvZK5wjeDqmYx4udC3zx9oFwm",
              "balances": {
                "BTC": 333600,
                "XCP": 399876544
              }
            }
          ]
        },
        "total": {
          "BTC": 807814,
          "XCP": 599845207
        }
      }
    }

balances
========

Get balances for address or current wallet.

Arguments
---------

 * asset (str, default=None): Optionally filter for given asset.
 * address (str, default=None): Optionally provide address to check, uses wallet by default

Returns
-------

.. code::

    Dict mapping asset to available quantity in satoshis,
    Unconfirmed assets are ignored.

    {
        "BTC": 926109330,
        "XCP": 140982404156
    }


blocksend
=========

Send funds using via blockchain transaction.

Arguments
---------

 * asset (str): Asset to send.
 * destination (address): Address to receive the funds.
 * quantity (int): Quantity of the given asset to transfer.
 * extra_btc (int, default=0): Optional bitcoin to also be sent.

Returns
-------

.. code::

    txid of published transaction.

connect
=======

Create micropayment connection with hub.

Arguments
---------

 * asset (str): Asset to exchange in connection.
 * quantity (str): Quantity to be bound in the deposit, this determins the maximum amount that can bet transferred.
 * expire_time (int, default=1024): Time in blocks after which the deposit expires and can be recovered.
 * delay_time (int, default=2): Blocks hub must wait before payout, protects against publish revoked commits.

Returns
-------

.. code::

    {
        "send_deposit_txid": "published bitcoin transaction id",
        "handle": "handle for created connection"
    }


microsend
=========

Send fund to via micropayment channel.

Arguments
---------

 * source (str): Handle of connection to send funds from.
 * destination (str): Handle of connection to receive funds.
 * quantity (int): Quantity of channel asset to transfer.
 * token (str, default=None): Optional token payee will receive with the payment.

Returns
-------

.. code::

    Provided token or generated token if None given.


status
======

Get status of connections and wallet.

Arguments
---------

 * handle (str, default=None): Optionally limit to given handle.
 * verbose (bool, default=False): Optionally show additional information.

Returns
-------

.. code::

    {
      "connections": {
        "a0b206d1f68edb1aa24084752b5693a9022349dc547fb9952aa510003e93": {
          "asset": "XCP",
          "balance": 31337,
          "status": "open",
          "ttl": 404
        }
      },
      "wallet": {
        "address": "n2WQGAvnDS1vf7uXToLou6kLxJXRGFHo2b",
        "balances": {
          "BTC": 926109330,
          "XCP": 140982404156
        }
      }
    }


sync
====

Sync open and recover funds from closed connections.

This WILL cost a fee per channnel synced as defined in the hub terms.

 * Synchronize open connections to send/receive payments.
 * Recover funds of closed connections.

Arguments
---------

 * handle (str, default=None): Optionally limit to given handle.

Returns
-------

.. code::

    {
      "connection handle": {
        "txids": ["of transactions publish while recovering funds"],
        "received_payments": [
          {
            "payer_handle": "sender handle",
            "amount": 1337,
            "token": "provided by sender"
          }
        ]
      }
    }


close
=====

Close open connection and settle to blockchain.
