# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <f483@storj.io>
# License: MIT (see LICENSE file)


import os
import argparse


def parse(args):

    # pre parse testnet to modify defaults depending on network
    testnet = "--testnet" in args

    description = "Decentral micropayment hub for counterparty assets."
    parser = argparse.ArgumentParser(description=description)

    # network to use
    parser.add_argument(
        '--testnet', action='store_true', help="Use bitcoin testnet."
    )

    # basedir path
    default = os.path.join(os.path.expanduser("~"), ".picopayments")
    parser.add_argument(
        '--basedir', default=default, metavar="PATH",
        help="Location of app files: {0}".format(default)
    )

    # show version
    parser.add_argument(
        '--version', action='store_true', help="Show version number."
    )

    # show hub terms
    parser.add_argument(
        '--hub-status', action='store_true', help="Get current hub status."
    )

    # get balances for given address
    parser.add_argument(
        '--get-balances', action='store_true',
        help="Get balances for wallet or given address."
    )

    # send funds to given address.
    parser.add_argument(
        '--blockchain-send', action='store_true',
        help="Send funds to given address."
    )
    parser.add_argument(
        '--destination', default=None, metavar="ADDRESS",
        help="FIXME doc string"
    )
    parser.add_argument(
        '--quantity', default=None, metavar="SATOSHIS",
        help="FIXME doc string"
    )
    parser.add_argument(
        '--extra-btc', default=0, metavar="SATOSHIS",
        help="FIXME doc string"
    )

    # start rpc api server
    parser.add_argument(
        '--serve', action='store_true',
        help="Start RPC-API server."
    )
    parser.add_argument(
        '--host', default="localhost", metavar="PORT",
        help="RPC-API server host: {0}".format("localhost")
    )
    default = 16000 if testnet else 6000
    parser.add_argument(
        '--port', type=int, default=default, metavar="PORT",
        help="RPC-API server port: {0}".format(default)
    )

    # generic options
    parser.add_argument(
        '--handle', default=None, metavar="HANDLE",
        help="FIXME doc string"
    )
    parser.add_argument(
        '--asset', default=None, metavar="ASSET",
        help="FIXME doc string"
    )

    # filter state
    parser.add_argument(
        '--connecting', action='store_true',
        help="Filter result open connections."
    )
    parser.add_argument(
        '--open', action='store_true',
        help="Filter result open connections."
    )
    parser.add_argument(
        '--closed', action='store_true',
        help="Filter result open connections."
    )

    return vars(parser.parse_args(args=args))
