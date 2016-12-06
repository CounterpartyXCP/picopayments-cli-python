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

    # # logging options
    # parser.add_argument(
    #     '--debug', action='store_true', help="Maximum logging."
    # )
    # parser.add_argument(
    #     '--verbose', action='store_true', help="Maximum logging."
    # )
    # parser.add_argument(
    #     '--quite', action='store_true', help="Minimum logging."
    # )

    # show version
    parser.add_argument(
        '--version', action='store_true', help="Show version number."
    )

    # show hub terms
    parser.add_argument(
        '--terms', action='store_true', help="Show hub terms."
    )

    # picopayments hub
    default_port = 15000 if testnet else 5000
    default = "https://127.0.0.1:{0}/api/".format(default_port)
    parser.add_argument(
        '--hub-url', default=default, metavar="URL",
        help="Picopayments hub api: {0}".format(default)
    )
    parser.add_argument(
        '--hub-username', default=None, metavar="VALUE",
        help="Picopayments hub username."
    )
    parser.add_argument(
        '--hub-password', default=None, metavar="VALUE",
        help="Picopayments hub password."
    )
    parser.add_argument(
        '--hub-skip-verify-cert', action='store_true',
        help="Skip ssl cert verification."
    )

    # start rpc api server
    parser.add_argument(
        '--srv-start', action='store_true',
        help="Start RPC-API server."
    )
    parser.add_argument(
        '--srv-host', default="localhost", metavar="PORT",
        help="RPC-API server host: {0}".format("localhost")
    )
    default = 16000 if testnet else 6000
    parser.add_argument(
        '--srv-port', type=int, default=default, metavar="PORT",
        help="RPC-API server port: {0}".format(default)
    )

    # generic options
    parser.add_argument(
        '--handle', default=None, metavar="HANDLE",
        help="Filter result by connection handle."
    )
    parser.add_argument(
        '--asset', default=None, metavar="ASSET",
        help="Filter result by asset."
    )
    parser.add_argument(
        '--quantity', default=None, metavar="HANDLE",
        help="Filter result by connection handle."
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
