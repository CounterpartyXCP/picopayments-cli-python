################
PicoPayments CLI
################

|BuildLink|_ |CoverageLink|_ |LicenseLink|_ |IssuesLink|_


.. |BuildLink| image:: https://travis-ci.org/StorjRND/picopayments-cli-python.svg
.. _BuildLink: https://travis-ci.org/StorjRND/picopayments-cli-python

.. |CoverageLink| image:: https://coveralls.io/repos/StorjRND/picopayments-cli-python/badge.svg
.. _CoverageLink: https://coveralls.io/r/StorjRND/picopayments-cli-python

.. |LicenseLink| image:: https://img.shields.io/badge/license-MIT-blue.svg
.. _LicenseLink: https://raw.githubusercontent.com/F483/picopayments-cli-python/master/LICENSE

.. |IssuesLink| image:: https://img.shields.io/github/issues/F483/picopayments-cli-python.svg
.. _IssuesLink: https://github.com/F483/picopayments-cli-python/issues


Micropayment hub CLI interface for counterparty assets.

Currently Python 3 is the supported version.


Setup
#####

.. code:: bash

    $ pip3 install picopayments-cli


Usage
#####

.. code:: bash

    $ picopayments-cli [config arguments] <command> [command arguments]


Usage examples
==============


.. code:: bash

    # show help text
    $ picopayments-cli --help

    # show help text for command
    $ picopayments-cli <command> --help

    # Show status of current connections
    $ picopayments-cli --testnet status

    # connect to hub
    $ picopayments-cli --testnet connect ASSET QUANTITY

    # queue payment
    $ picopayments-cli --testnet queuepayment SOURCEHANDLE DESTINATIONHANDLE QUANTITY

    # sync payments
    $ picopayments-cli --testnet sync

    # close payment channel
    $ picopayments-cli --testnet close HANDLE


API Calls/Commands
##################


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


queuepayment
============

Queue micropayment channel send (sent on sync).


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


Testing guide
#############

Please be liberal in opening an issue here on this github project with any
problems or questions you have, well repsond as soon as I can.

Please note that all testing is currently on testnet only using the
counterparty XCP asset.


.. code:: bash

    # install the picopayments cli client (sorry no gui wallet just yet)
    $ pip3 install picopayments-cli
    
    # Show status of current connections and wallet
    $ picopayments-cli --testnet status
    # post the wallet address in https://community.storj.io/channel/micropayments-testing and you will be sent some funds for testing

    # connect to hub (prints the hex handle of the created channel)
    $ picopayments-cli --testnet connect XCP 1000000

    # you will have to wait until your deposit is confirmed, then the hub
    # will match your deposit so you can recieve funds. After the hub deposit
    # is confirmed the micropayment channel is open for use.

    # Show status of current connections and wallet
    $ picopayments-cli --testnet status
    
    # Show hub status: open connections, liquidity, terms and funding addresses
    $ picopayments-cli --testnet hubstatus

    # queue payment
    $ picopayments-cli --testnet queuepayment SOURCEHANDLE DESTINATIONHANDLE QUANTITY

    # do not send more then you have or the other party can receive or it
    # will mess up the channel (known issue I have to fix)

    # sync payments (cost 1 xcp fee)
    $ picopayments-cli --testnet sync
    
    # close payment channel and settle to blockchain
    $ picopayments-cli --testnet close HANDLE


FAQ
###

TODO answered questions
