import os
import pycoin
from pycoin.tx import Tx
from pycoin.serialize import b2h  # NOQA
from pycoin.serialize import h2b  # NOQA
from pycoin.serialize import b2h_rev  # NOQA
from pycoin.encoding import hash160
from pycoin.key.BIP32Node import BIP32Node
from pycoin.key import Key
from pycoin.encoding import sec_to_public_pair, public_pair_to_sec, to_bytes_32


def gettxid(rawtx):
    tx = Tx.from_hex(rawtx)
    return b2h_rev(tx.hash())


def random_wif(netcode="BTC"):
    return BIP32Node.from_master_secret(os.urandom(32), netcode=netcode).wif()


def wif2sec(wif):
    return Key.from_text(wif).sec()


def wif2pubkey(wif):
    return b2h(wif2sec(wif))


def wif2address(wif):
    return Key.from_text(wif).address()


def wif2privkey(wif):
    secret_exp = Key.from_text(wif).secret_exponent()
    return to_bytes_32(secret_exp)


def wif2netcode(wif):
    return Key.from_text(wif).netcode()


def decode_pubkey(pubkey):
    """Decode compressed hex pubkey."""
    compressed_pubkey = h2b(pubkey)
    public_pair = sec_to_public_pair(compressed_pubkey)
    return public_pair_to_sec(public_pair, compressed=False)


def pubkey2address(pubkey, netcode="BTC"):
    return sec2address(h2b(pubkey), netcode=netcode)


def sec2address(sec, netcode="BTC"):
    prefix = pycoin.networks.address_prefix_for_netcode(netcode)
    return pycoin.encoding.hash160_sec_to_bitcoin_address(hash160(sec), prefix)


def script2address(script_hex, netcode="BTC"):
    return pycoin.tx.pay_to.address_for_pay_to_script(
        h2b(script_hex), netcode=netcode
    )


def hash160hex(hexdata):
    return b2h(hash160(h2b(hexdata)))


def tosatoshis(btcamount):
    return int(btcamount * 100000000)
