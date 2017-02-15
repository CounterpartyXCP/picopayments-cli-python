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


searchrawtxs
============

Get raw transactions for given address.

Arguments
---------

 * address (str): Address to get raw transactions for.
 * unconfirmed (bool, default=true): Include unconfirmed transactions.

Returns
-------

A list of dicts with information about the transaction.

Example
-------

.. code::

    $ picopayments-cli --testnet searchrawtxs n2s5WgXPZvgKjtApHLk294gCditcDEKGJS
    [
        {
            "blockhash": "0000000000000a835cdd31ad68496bd41c240471a5cdff3c07924646d441bd78",
            "blocktime": 1487152958,
            "confirmations": 31,
            "hex": "010000000135a32ea67f349fcae4bd272285663eec97c37bb2b816303bc44b26992b551cd9010000006a47304402207a89d42e1e61c7abead529b09f039ba2d3c585db88ddb233f9bb360cccd5c07002204ae361cc83610beb406b690bc62fad5af13d79919e724f039675f555c01b2b670121035f57228dc3b9a3224f2d48a1e2f9886f8412a0e77afdec28fd94dab7c7513b56ffffffff0340420f00000000001976a914ea28fc5a328d7f43c4a88e7a2edf1e1d8a8d60ae88ac00000000000000001e6a1c594663b76ecc1e31edd16d3b1ec19b0f4f983a71a70bed9465caa1cd8afc7100000000001976a914e63fe6f12b3300f2fad00a1270b71529985d972d88ac00000000",
            "locktime": 0,
            "size": 264,
            "time": 1487152958,
            "txid": "caf1f644777ed7b2b3eb6b5870368efe678eef738ba9c269560ad4414b3d1ce5",
            "version": 1,
            "vin": [
                {
                    "scriptSig": {
                        "asm": "304402207a89d42e1e61c7abead529b09f039ba2d3c585db88ddb233f9bb360cccd5c07002204ae361cc83610beb406b690bc62fad5af13d79919e724f039675f555c01b2b67[ALL] 035f57228dc3b9a3224f2d48a1e2f9886f8412a0e77afdec28fd94dab7c7513b56",
                        "hex": "47304402207a89d42e1e61c7abead529b09f039ba2d3c585db88ddb233f9bb360cccd5c07002204ae361cc83610beb406b690bc62fad5af13d79919e724f039675f555c01b2b670121035f57228dc3b9a3224f2d48a1e2f9886f8412a0e77afdec28fd94dab7c7513b56"
                    },
                    "sequence": 4294967295,
                    "txid": "d91c552b99264bc43b3016b8b27bc397ec3e66852227bde4ca9f347fa62ea335",
                    "vout": 1
                }
            ],
            "vout": [
                {
                    "n": 0,
                    "scriptPubKey": {
                        "addresses": [
                            "n2s5WgXPZvgKjtApHLk294gCditcDEKGJS"
                        ],
                        "asm": "OP_DUP OP_HASH160 ea28fc5a328d7f43c4a88e7a2edf1e1d8a8d60ae OP_EQUALVERIFY OP_CHECKSIG",
                        "hex": "76a914ea28fc5a328d7f43c4a88e7a2edf1e1d8a8d60ae88ac",
                        "reqSigs": 1,
                        "type": "pubkeyhash"
                    },
                    "value": 0.01
                },
                {
                    "n": 1,
                    "scriptPubKey": {
                        "asm": "OP_RETURN 594663b76ecc1e31edd16d3b1ec19b0f4f983a71a70bed9465caa1cd",
                        "hex": "6a1c594663b76ecc1e31edd16d3b1ec19b0f4f983a71a70bed9465caa1cd",
                        "type": "nulldata"
                    },
                    "value": 0.0
                },
                {
                    "n": 2,
                    "scriptPubKey": {
                        "addresses": [
                            "n2WQGAvnDS1vf7uXToLou6kLxJXRGFHo2b"
                        ],
                        "asm": "OP_DUP OP_HASH160 e63fe6f12b3300f2fad00a1270b71529985d972d OP_EQUALVERIFY OP_CHECKSIG",
                        "hex": "76a914e63fe6f12b3300f2fad00a1270b71529985d972d88ac",
                        "reqSigs": 1,
                        "type": "pubkeyhash"
                    },
                    "value": 0.07470218
                }
            ]
        }
    ]

listutxos
=========

Get utxos for given address.

Arguments
---------

 * address (str): Address to get utxos for.
 * unconfirmed (bool, default=true): Include unconfirmed outputs.

Returns
-------

A list of dicts with information the unspent transaction output.

Example
-------

.. code::

    $ picopayments-cli --testnet listutxos n2s5WgXPZvgKjtApHLk294gCditcDEKGJS
    [
        {
            "amount": 0.01,
            "confirmations": 32,
            "scriptPubKey": "76a914ea28fc5a328d7f43c4a88e7a2edf1e1d8a8d60ae88ac",
            "txid": "caf1f644777ed7b2b3eb6b5870368efe678eef738ba9c269560ad4414b3d1ce5",
            "vout": 0
        }
    ]


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


history
=======

Show history

Arguments
---------

 * handle (str): Limit history to given channel.

Returns
-------

List of previous actions made.


cull
====

Removes closed channels if all funds have been recovered.

Arguments
---------

 * handle (str): Optional handle of specific connection to be cull.

Returns
-------

List of with handles of culled connections.


serve
=====

Start RPC-API Server.

Arguments
---------

 * host (str): Network interface on which to host the service.
 * port (int): Network port on which to host the service.


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
