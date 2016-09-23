# coding: utf-8
# Copyright (c) 2016 Fabian Barkhau <fabian.barkhau@gmail.com>
# License: MIT (see LICENSE file)


import pycoin
from pycoin.key import Key
from pycoin.tx import Tx
from pycoin.tx.script import tools
from pycoin.encoding import hash160
from pycoin.tx.pay_to import SUBCLASSES
from pycoin.serialize import b2h, h2b, b2h_rev
from pycoin.tx.pay_to.ScriptType import DEFAULT_PLACEHOLDER_SIGNATURE
from pycoin.tx.pay_to.ScriptType import ScriptType
from pycoin import encoding
from pycoin.tx.script.check_signature import parse_signature_blob
from pycoin.tx.script.der import UnexpectedDER
from pycoin import ecdsa


MAX_SEQUENCE = 0x0000FFFF
DEPOSIT_SCRIPT = """
    OP_IF
        2 {payer_pubkey} {payee_pubkey} 2 OP_CHECKMULTISIG
    OP_ELSE
        OP_IF
            OP_HASH160 {spend_secret_hash} OP_EQUALVERIFY
            {payer_pubkey} OP_CHECKSIG
        OP_ELSE
            {expire_time} OP_NOP3 OP_DROP
            {payer_pubkey} OP_CHECKSIG
        OP_ENDIF
    OP_ENDIF
"""
COMMIT_SCRIPT = """
    OP_IF
        {delay_time} OP_NOP3 OP_DROP
        OP_HASH160 {spend_secret_hash} OP_EQUALVERIFY
        {payee_pubkey} OP_CHECKSIG
    OP_ELSE
        OP_HASH160 {revoke_secret_hash} OP_EQUALVERIFY
        {payer_pubkey} OP_CHECKSIG
    OP_ENDIF
"""
EXPIRE_SCRIPTSIG = "{sig} OP_0 OP_0"
CHANGE_SCRIPTSIG = "{sig} {secret} OP_1 OP_0"
COMMIT_SCRIPTSIG = "OP_0 {payer_sig} {payee_sig} OP_1"
PAYOUT_SCRIPTSIG = "{sig} {spend_secret} OP_1"
REVOKE_SCRIPTSIG = "{sig} {revoke_secret} OP_0"


# FIXME add simple functions to validate transactions


class InvalidScript(Exception):

    def __init__(self, x):
        msg = "Invalid script: '{0}'"
        super(InvalidScript, self).__init__(msg.format(x))


class InvalidPayerSignature(Exception):

    def __init__(self):
        msg = "Invalid or missing payer signature!"
        super(InvalidPayerSignature, self).__init__(msg)


class InvalidSequenceValue(Exception):

    def __init__(self, x):
        msg = "Invalid sequence value: {0}"
        super(InvalidSequenceValue, self).__init__(msg.format(x))


class InvalidSignature(Exception):

    def __init__(self, pubkey, signature, data):
        msg = "Invalid signature for pubkey {0}, signature {1}, data {2}"
        super(InvalidSignature, self).__init__(
            msg.format(pubkey, signature, data)
        )


def _get_word(script_bin, index):
    pc = 0
    i = 0
    while pc < len(script_bin) and i <= index:
        opcode, data, pc = tools.get_opcode(script_bin, pc)
        i += 1
    if i != index + 1:
        raise ValueError(index)
    return opcode, data, tools.disassemble_for_opcode_data(opcode, data)


def validate(reference_script_hex, untrusted_script_hex):
    ref_script_bin = h2b(reference_script_hex)
    untrusted_script_bin = h2b(untrusted_script_hex)
    r_pc = 0
    u_pc = 0
    while r_pc < len(ref_script_bin) and u_pc < len(untrusted_script_bin):
        r_opcode, r_data, r_pc = tools.get_opcode(ref_script_bin, r_pc)
        u_opcode, u_data, u_pc = tools.get_opcode(untrusted_script_bin, u_pc)
        if r_data is not None and b2h(r_data) == "deadbeef":
            continue  # placeholder for expected variable
        if r_opcode != u_opcode or r_data != u_data:
            raise InvalidScript(b2h(untrusted_script_bin))
    if r_pc != len(ref_script_bin) or u_pc != len(untrusted_script_bin):
        raise InvalidScript(b2h(untrusted_script_bin))


def validate_deposit_script(deposit_script_hex, validate_expire_time=True):
    reference_script_hex = compile_deposit_script(
        "deadbeef", "deadbeef", "deadbeef", "deadbeef"
    )
    validate(reference_script_hex, deposit_script_hex)
    if validate_expire_time:
        get_deposit_expire_time(deposit_script_hex)  # has valid sequence value


def validate_commit_script(commit_script_hex, validate_delay_time=True):
    reference_script_hex = compile_commit_script(
        "deadbeef", "deadbeef", "deadbeef", "deadbeef", "deadbeef"
    )
    validate(reference_script_hex, commit_script_hex)
    if validate_delay_time:
        get_commit_delay_time(commit_script_hex)  # has valid sequence value


def get_spend_secret(payout_rawtx, commit_script_hex):
    validate_commit_script(commit_script_hex)
    commit_script_bin = h2b(commit_script_hex)
    tx = Tx.from_hex(payout_rawtx)
    spend_script_bin = tx.txs_in[0].script
    try:
        opcode, data, disassembled = _get_word(spend_script_bin, 3)
        if data == commit_script_bin:  # is payout tx
            opcode, spend_secret, disassembled = _get_word(spend_script_bin, 1)
            return b2h(spend_secret)
    except ValueError:
        return None


def _parse_sequence_value(opcode, data, disassembled):
    value = None
    if opcode == 0:
        value = 0
    elif 0 < opcode < 76:  # get from data bytes
        value = tools.int_from_script_bytes(data)
    elif 80 < opcode < 97:  # OP_1 - OP_16
        value = opcode - 80
    if not (MAX_SEQUENCE >= value >= 0):
        raise InvalidSequenceValue(disassembled)
    return value


def get_commit_payer_pubkey(script_hex):
    validate_commit_script(script_hex)
    opcode, data, disassembled = _get_word(h2b(script_hex), 13)
    return b2h(data)


def get_commit_payee_pubkey(script_hex):
    validate_commit_script(script_hex)
    opcode, data, disassembled = _get_word(h2b(script_hex), 7)
    return b2h(data)


def get_commit_delay_time(script_hex):
    validate_commit_script(script_hex, validate_delay_time=False)
    opcode, data, disassembled = _get_word(h2b(script_hex), 1)
    return _parse_sequence_value(opcode, data, disassembled)


def get_commit_spend_secret_hash(script_hex):
    validate_commit_script(script_hex)
    opcode, data, disassembled = _get_word(h2b(script_hex), 5)
    return b2h(data)


def get_commit_revoke_secret_hash(script_hex):
    validate_commit_script(script_hex)
    opcode, data, disassembled = _get_word(h2b(script_hex), 11)
    return b2h(data)


def get_deposit_payer_pubkey(script_hex):
    validate_deposit_script(script_hex)
    opcode, data, disassembled = _get_word(h2b(script_hex), 2)
    return b2h(data)


def get_deposit_payee_pubkey(script_hex):
    validate_deposit_script(script_hex)
    opcode, data, disassembled = _get_word(h2b(script_hex), 3)
    return b2h(data)


def get_deposit_expire_time(script_hex):
    validate_deposit_script(script_hex, validate_expire_time=False)
    opcode, data, disassembled = _get_word(h2b(script_hex), 14)
    return _parse_sequence_value(opcode, data, disassembled)


def get_deposit_spend_secret_hash(script_hex):
    validate_deposit_script(script_hex)
    opcode, data, disassembled = _get_word(h2b(script_hex), 9)
    return b2h(data)


def compile_deposit_script(payer_pubkey, payee_pubkey,
                           spend_secret_hash, expire_time):
    """Compile deposit transaction pay ot script.

    Args:
        payer_pubkey (str): Hex encoded public key in sec format.
        payee_pubkey (str): Hex encoded public key in sec format.
        spend_secret_hash (str): Hex encoded hash160 of spend secret.
        expire_time (int): Channel expire time in blocks given as int.

    Return:
        Compiled bitcoin script.
    """
    script_asm = DEPOSIT_SCRIPT.format(
        payer_pubkey=payer_pubkey,
        payee_pubkey=payee_pubkey,
        spend_secret_hash=spend_secret_hash,
        expire_time=str(expire_time)
    )
    return b2h(tools.compile(script_asm))


def compile_commit_script(payer_pubkey, payee_pubkey, spend_secret_hash,
                          revoke_secret_hash, delay_time):
    script_asm = COMMIT_SCRIPT.format(
        payer_pubkey=payer_pubkey,
        payee_pubkey=payee_pubkey,
        spend_secret_hash=spend_secret_hash,
        revoke_secret_hash=revoke_secret_hash,
        delay_time=str(delay_time)
    )
    return b2h(tools.compile(script_asm))


def compile_commit_scriptsig(payer_sig, payee_sig, deposit_script_hex):
    sig_asm = COMMIT_SCRIPTSIG.format(
        payer_sig=payer_sig, payee_sig=payee_sig
    )
    return b2h(tools.compile("{0} {1}".format(sig_asm, deposit_script_hex)))


def sign_deposit(get_tx_func, payer_wif, rawtx):
    tx = _load_tx(get_tx_func, rawtx)
    key = Key.from_text(payer_wif)
    secret_exponents = [key.secret_exponent()]
    hash160_lookup = pycoin.tx.pay_to.build_hash160_lookup(secret_exponents)
    tx.sign(hash160_lookup)
    return tx.as_hex()


def sign_created_commit(get_tx_func, payer_wif, rawtx, deposit_script_hex):
    validate_deposit_script(deposit_script_hex)
    tx = _load_tx(get_tx_func, rawtx)
    expire_time = get_deposit_expire_time(deposit_script_hex)
    hash160_lookup, p2sh_lookup = _make_lookups(payer_wif, deposit_script_hex)
    hash160_lookup, p2sh_lookup = _make_lookups(payer_wif, deposit_script_hex)
    with _DepositScriptHandler(expire_time):
        tx.sign(hash160_lookup, p2sh_lookup=p2sh_lookup,
                spend_type="create_commit", spend_secret=None)
    return tx.as_hex()


def sign_finalize_commit(get_tx_func, payee_wif, rawtx, deposit_script_hex):
    validate_deposit_script(deposit_script_hex)
    tx = _load_tx(get_tx_func, rawtx)
    expire_time = get_deposit_expire_time(deposit_script_hex)
    hash160_lookup, p2sh_lookup = _make_lookups(payee_wif, deposit_script_hex)
    with _DepositScriptHandler(expire_time):
        tx.sign(hash160_lookup, p2sh_lookup=p2sh_lookup,
                spend_type="finalize_commit", spend_secret=None)
    assert(tx.bad_signature_count() == 0)
    return tx.as_hex()


def sign_revoke_recover(get_tx_func, payer_wif, rawtx,
                        commit_script_hex, revoke_secret):
    validate_commit_script(commit_script_hex)
    return _sign_commit_recover(get_tx_func, payer_wif, rawtx,
                                commit_script_hex, "revoke",
                                None, revoke_secret)


def sign_payout_recover(get_tx_func, payee_wif, rawtx,
                        commit_script_hex, spend_secret):
    validate_commit_script(commit_script_hex)
    return _sign_commit_recover(get_tx_func, payee_wif, rawtx,
                                commit_script_hex, "payout",
                                spend_secret, None)


def sign_change_recover(get_tx_func, payer_wif, rawtx,
                        deposit_script_hex, spend_secret):
    validate_deposit_script(deposit_script_hex)
    return _sign_deposit_recover(
        get_tx_func, payer_wif, rawtx,
        deposit_script_hex, "change", spend_secret
    )


def sign_expire_recover(get_tx_func, payer_wif, rawtx, deposit_script_hex):
    validate_deposit_script(deposit_script_hex)
    return _sign_deposit_recover(
        get_tx_func, payer_wif, rawtx, deposit_script_hex, "expire", None
    )


def _load_tx(get_tx_func, rawtx):
    tx = Tx.from_hex(rawtx)
    # FIXME batch load to reduce traffic or better yet remove need altogether
    for txin in tx.txs_in:
        utxo_tx = Tx.from_hex(get_tx_func(b2h_rev(txin.previous_hash)))
        tx.unspents.append(utxo_tx.txs_out[txin.previous_index])
    return tx


def _sign_deposit_recover(get_tx_func, wif, rawtx, script_hex,
                          spend_type, spend_secret):
    tx = _load_tx(get_tx_func, rawtx)
    expire_time = get_deposit_expire_time(script_hex)
    hash160_lookup, p2sh_lookup = _make_lookups(wif, script_hex)
    with _DepositScriptHandler(expire_time):
        tx.sign(hash160_lookup, p2sh_lookup=p2sh_lookup,
                spend_type=spend_type, spend_secret=spend_secret)
    assert(tx.bad_signature_count() == 0)
    return tx.as_hex()


def _sign_commit_recover(get_tx_func, wif, rawtx, script_hex, spend_type,
                         spend_secret, revoke_secret):
    tx = _load_tx(get_tx_func, rawtx)
    delay_time = get_commit_delay_time(script_hex)
    hash160_lookup, p2sh_lookup = _make_lookups(wif, script_hex)
    with _CommitScriptHandler(delay_time):
        tx.sign(hash160_lookup, p2sh_lookup=p2sh_lookup,
                spend_type=spend_type, spend_secret=spend_secret,
                revoke_secret=revoke_secret)
    assert(tx.bad_signature_count() == 0)
    return tx.as_hex()


def _make_lookups(wif, script_hex):
    script_bin = h2b(script_hex)
    hash160_lookup = pycoin.tx.pay_to.build_hash160_lookup(
        [pycoin.key.Key.from_text(wif).secret_exponent()]
    )
    p2sh_lookup = pycoin.tx.pay_to.build_p2sh_lookup([script_bin])
    return hash160_lookup, p2sh_lookup


class _AbsCommitScript(ScriptType):

    def __init__(self, delay_time, spend_secret_hash,
                 payee_sec, payer_sec, revoke_secret_hash):
        self.delay_time = delay_time
        self.spend_secret_hash = spend_secret_hash
        self.payee_sec = payee_sec
        self.payer_sec = payer_sec
        self.revoke_secret_hash = revoke_secret_hash
        self.script = h2b(compile_commit_script(
            b2h(payer_sec), b2h(payee_sec), spend_secret_hash,
            revoke_secret_hash, delay_time
        ))

    @classmethod
    def from_script(cls, script):
        r = cls.match(script)
        if r:
            delay_time = get_commit_delay_time(b2h(cls.TEMPLATE))
            spend_secret_hash = b2h(r["PUBKEYHASH_LIST"][0])
            payee_sec = r["PUBKEY_LIST"][0]
            revoke_secret_hash = b2h(r["PUBKEYHASH_LIST"][1])
            payer_sec = r["PUBKEY_LIST"][1]
            obj = cls(delay_time, spend_secret_hash,
                      payee_sec, payer_sec, revoke_secret_hash)
            assert(obj.script == script)
            return obj
        raise ValueError("bad script")  # pragma: no cover

    def solve_payout(self, **kwargs):
        hash160_lookup = kwargs["hash160_lookup"]
        spend_secret = kwargs["spend_secret"]
        private_key = hash160_lookup.get(encoding.hash160(self.payee_sec))
        secret_exponent, public_pair, compressed = private_key
        sig = self._create_script_signature(
            secret_exponent, kwargs["sign_value"], kwargs["signature_type"]
        )
        return tools.compile(PAYOUT_SCRIPTSIG.format(
            sig=b2h(sig), spend_secret=spend_secret
        ))

    def solve_revoke(self, **kwargs):
        hash160_lookup = kwargs["hash160_lookup"]
        revoke_secret = kwargs["revoke_secret"]
        private_key = hash160_lookup.get(encoding.hash160(self.payer_sec))
        secret_exponent, public_pair, compressed = private_key
        sig = self._create_script_signature(
            secret_exponent, kwargs["sign_value"], kwargs["signature_type"]
        )
        return tools.compile(REVOKE_SCRIPTSIG.format(
            sig=b2h(sig), revoke_secret=revoke_secret
        ))

    def solve(self, **kwargs):
        solve_methods = {
            "payout": self.solve_payout,
            "revoke": self.solve_revoke,
        }
        solve_method = solve_methods[kwargs["spend_type"]]
        return solve_method(**kwargs)


class _AbsDepositScript(ScriptType):

    def __init__(self, payer_sec, payee_sec, spend_secret_hash, expire_time):
        self.payer_sec = payer_sec
        self.payee_sec = payee_sec
        self.spend_secret_hash = spend_secret_hash
        self.expire_time = expire_time
        self.script = h2b(compile_deposit_script(
            b2h(payer_sec), b2h(payee_sec), spend_secret_hash, expire_time
        ))

    @classmethod
    def from_script(cls, script):
        r = cls.match(script)
        if r:
            payer_sec = r["PUBKEY_LIST"][0]
            payee_sec = r["PUBKEY_LIST"][1]
            assert(payer_sec == r["PUBKEY_LIST"][2])
            assert(payer_sec == r["PUBKEY_LIST"][3])
            spend_secret_hash = b2h(r["PUBKEYHASH_LIST"][0])
            expire_time = get_deposit_expire_time(b2h(cls.TEMPLATE))
            obj = cls(payer_sec, payee_sec, spend_secret_hash, expire_time)
            assert(obj.script == script)
            return obj
        raise ValueError("bad script")  # pragma: no cover

    def solve_expire(self, **kwargs):
        hash160_lookup = kwargs["hash160_lookup"]
        private_key = hash160_lookup.get(encoding.hash160(self.payer_sec))
        secret_exponent, public_pair, compressed = private_key
        sig = self._create_script_signature(
            secret_exponent, kwargs["sign_value"], kwargs["signature_type"]
        )
        return tools.compile(EXPIRE_SCRIPTSIG.format(sig=b2h(sig)))

    def solve_change(self, **kwargs):
        hash160_lookup = kwargs["hash160_lookup"]
        spend_secret = kwargs["spend_secret"]
        private_key = hash160_lookup.get(encoding.hash160(self.payer_sec))
        secret_exponent, public_pair, compressed = private_key
        sig = self._create_script_signature(
            secret_exponent, kwargs["sign_value"], kwargs["signature_type"]
        )
        spend_secret_hash = get_deposit_spend_secret_hash(b2h(self.script))
        provided_spend_secret_hash = b2h(hash160(h2b(spend_secret)))
        assert(spend_secret_hash == provided_spend_secret_hash)
        script_asm = CHANGE_SCRIPTSIG.format(
            sig=b2h(sig), secret=spend_secret
        )
        return tools.compile(script_asm)

    def solve_create_commit(self, **kwargs):
        hash160_lookup = kwargs["hash160_lookup"]
        private_key = hash160_lookup.get(encoding.hash160(self.payer_sec))
        secret_exponent, public_pair, compressed = private_key
        sig = self._create_script_signature(
            secret_exponent, kwargs["sign_value"], kwargs["signature_type"]
        )
        signature_placeholder = kwargs.get("signature_placeholder",
                                           DEFAULT_PLACEHOLDER_SIGNATURE)
        script_asm = COMMIT_SCRIPTSIG.format(
            payer_sig=b2h(sig), payee_sig=b2h(signature_placeholder)
        )
        return tools.compile(script_asm)

    def solve_finalize_commit(self, **kwargs):
        hash160_lookup = kwargs.get("hash160_lookup")
        sign_value = kwargs.get("sign_value")
        signature_type = kwargs.get("signature_type")
        existing_script = kwargs.get("existing_script")

        # validate payer sig
        try:
            opcode, data, pc = tools.get_opcode(existing_script, 0)  # OP_0
            opcode, payer_sig, pc = tools.get_opcode(existing_script, pc)
            sig_pair, actual_signature_type = parse_signature_blob(payer_sig)
            assert(signature_type == actual_signature_type)
            public_pair = encoding.sec_to_public_pair(self.payer_sec)
            sig_pair, signature_type = parse_signature_blob(payer_sig)
            valid = ecdsa.verify(ecdsa.generator_secp256k1, public_pair,
                                 sign_value, sig_pair)
            if not valid:
                raise InvalidPayerSignature()
        except UnexpectedDER:
            raise InvalidPayerSignature()
        except encoding.EncodingError:
            raise InvalidPayerSignature()

        # sign
        private_key = hash160_lookup.get(encoding.hash160(self.payee_sec))
        secret_exponent, public_pair, compressed = private_key
        payee_sig = self._create_script_signature(
            secret_exponent, sign_value, signature_type
        )

        script_asm = COMMIT_SCRIPTSIG.format(
            payer_sig=b2h(payer_sig), payee_sig=b2h(payee_sig)
        )
        return tools.compile(script_asm)

    def solve(self, **kwargs):
        solve_methods = {
            "expire": self.solve_expire,
            "change": self.solve_change,
            "create_commit": self.solve_create_commit,
            "finalize_commit": self.solve_finalize_commit
        }
        solve_method = solve_methods[kwargs["spend_type"]]
        return solve_method(**kwargs)


class _CommitScriptHandler():

    def __init__(self, delay_time):
        class CommitScript(_AbsCommitScript):
            TEMPLATE = h2b(compile_commit_script(
                "OP_PUBKEY", "OP_PUBKEY", "OP_PUBKEYHASH",
                "OP_PUBKEYHASH", delay_time
            ))
        self.script_handler = CommitScript

    def __enter__(self):
        SUBCLASSES.insert(0, self.script_handler)

    def __exit__(self, type, value, traceback):
        SUBCLASSES.pop(0)


class _DepositScriptHandler():

    def __init__(self, expire_time):
        class DepositScript(_AbsDepositScript):
            TEMPLATE = h2b(compile_deposit_script(
                "OP_PUBKEY", "OP_PUBKEY",
                "OP_PUBKEYHASH", expire_time
            ))
        self.script_handler = DepositScript

    def __enter__(self):
        SUBCLASSES.insert(0, self.script_handler)

    def __exit__(self, type, value, traceback):
        SUBCLASSES.pop(0)
