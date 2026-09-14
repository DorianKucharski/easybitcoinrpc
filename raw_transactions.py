from __future__ import annotations

from typing import Any, Literal, overload

from easybitcoinrpc.client import JsonRpcClient, RpcCall
from easybitcoinrpc.models import OutPoint, Transaction, TransactionSummary, Vout

class RawTransactions:
    def __init__(self, client: JsonRpcClient) -> None:
        self._client = client

    def analyze_psbt(self, psbt: str) -> dict[str, Any]:
        """
        Analyzes and provides information about the current status of a PSBT and its inputs.

        Parameters
        -------
        psbt : str
            A base64 string of a PSBT

        Returns
        -------
        dict
             Information about the current status of a PSBT and its inputs
        """
        return self._client.call("analyzepsbt", psbt)

    def combine_psbt(self, txs: dict[str, Any]) -> None:
        """
        Combine multiple partially signed Bitcoin transactions into one transaction. Implements the Combiner role.

        Parameters
        -------
        txs : dict
            A json array of base64 strings of partially signed transactions
        """
        self._client.call("combinepsbt", txs)

    def combine_raw_transaction(self, txs: dict[str, Any]) -> str:
        """
        Combine multiple partially signed transactions into one transaction.
        The combined transaction may be another partially signed transaction or a fully signed transaction.

        Parameters
        -------
        txs : dict
            A json array of hex strings of partially signed transactions.

        Returns
        -------
        str
            The hex-encoded raw transaction with signature(s).
        """
        return self._client.call("combinerawtransaction", txs)

    def convert_to_psbt(self, hexstring: str, permitsigdata: bool | None = None, iswitness: bool | None = None) -> None:
        """
        Converts a network serialized transaction to a PSBT. This should be used only with createrawtransaction and
        fundrawtransaction createpsbt and walletcreatefundedpsbt should be used for new applications.

        Parameters
        -------
        hexstring : str
            The hex string of a raw transaction.

        permitsigdata : bool
            If true, any signatures in the input will be discarded and conversion will continue.
            If false, RPC will fail if any signatures are present

        iswitness : bool
            Whether the transaction hex is a serialized witness transaction. If iswitness is not present,
            heuristic tests will be used in decoding. If true, only witness deserializaion will be tried. If false,
            only non-witness deserialization will be tried. Only has an effect if permitsigdata is true
        """
        self._client.call("converttopsbt", hexstring, permitsigdata, iswitness)

    def create_psbt(self, inputs: list[Any], outputs: list[Any], locktime: int | None = None, replaceable: bool | None = None) -> None:
        """
        Creates a transaction in the Partially Signed Transaction format. Implements the Creator role.

        Parameters
        -------
        inputs : list
            A json array of json objects

        outputs : list
            A json array with outputs (key-value pairs), where none of the keys are duplicated.
            That is, each address can only appear once and there can only be one ‘data’ object.
            For compatibility reasons, a dictionary, which holds the key-value pairs directly,
            is also accepted as second parameter.

        locktime : int
            Raw locktime. Non-0 value also locktime-activates inputs

        replaceable : bool
            Marks this transaction as BIP125 replaceable. Allows this transaction to be replaced by a transaction
            with higher fees. If provided, it is an error if explicit sequence numbers are incompatible.
        """
        self._client.call("createpsbt", inputs, outputs, locktime, replaceable)

    def create_raw_transaction(self, inputs: list[dict[str, Any]], outputs: list[dict[str, Any]] | dict[str, Any], locktime: int | None = None, replaceable: bool | None = None) -> str:
        """
        Create a transaction spending the given inputs and creating new outputs. Outputs can be addresses or data.
        Returns hex-encoded raw transaction. Note that the transaction’s inputs are not signed, and it is not stored
        in the wallet or transmitted to the network

        Parameters
        -------
        inputs : list
            A json array of json objects

        outputs : list
            A json array with outputs (key-value pairs), where none of the keys are duplicated.
            That is, each address can only appear once and there can only be one ‘data’ object.
            For compatibility reasons, a dictionary, which holds the key-value pairs directly,
            is also accepted as second parameter.

        locktime : int
            Raw locktime. Non-0 value also locktime-activates inputs.

        replaceable : bool
            Marks this transaction as BIP125-replaceable. Allows this transaction to be replaced by a transaction
            with higher fees. If provided, it is an error if explicit sequence numbers are incompatible.

        Returns
        -------
        str
            Hex string of the transaction
        """
        return self._client.call("createrawtransaction", inputs, outputs, locktime, replaceable)

    def decode_psbt(self, psbt: str) -> dict[str, Any]:
        """
        Return a JSON object representing the serialized, base64-encoded partially signed Bitcoin transaction.

        Parameters
        -------
        psbt : str
            The PSBT base64 string.

        Returns
        -------
        dict
            Object representing the serialized, base64-encoded partially signed Bitcoin transaction.
        """
        return self._client.call("decodepsbt", psbt)

    def decode_raw_transaction(self, hexstring: str, iswitness: bool | None = None) -> dict[str, Any]:
        """
        Return a JSON object representing the serialized, hex-encoded transaction.

        Parameters
        -------
        hexstring : str
            The transaction hex string

        iswitness : bool
            Whether the transaction hex is a serialized witness transaction.
            If iswitness is not present, heuristic tests will be used in decoding

        Returns
        -------
        dict
            Object representing the serialized, hex-encoded transaction.
        """
        return self._client.call("decoderawtransaction", hexstring, iswitness)

    def decode_script(self, hexstring: str) -> dict[str, Any]:
        """
        Decode a hex-encoded script.

        Parameters
        -------
        hexstring : str
            The hex-encoded script.

        Returns
        -------
        dict
            Decoded script.
        """
        return self._client.call("decodescript", hexstring)

    def finalize_psbt(self, psbt: str, extract: bool | None = None) -> dict[str, Any]:
        """
        Finalize the inputs of a PSBT. If the transaction is fully signed, it will produce a network serialized
        transaction which can be broadcast with sendrawtransaction. Otherwise a PSBT will be created which has
        the final_scriptSig and final_scriptWitness fields filled for inputs that are complete.
        Implements the Finalizer and Extractor roles.

        Parameters
        -------
        psbt : str
            A base64 string of a PSBT.

        extract : bool
            If true and the transaction is complete, extract and return the complete transaction in normal
            network serialization instead of the PSBT.

        Returns
        -------
        dict
            Object with PSBT, network serialized transaction and if it's complete.
        """
        return self._client.call("finalizepsbt", psbt, extract)

    def fund_raw_transaction(self, hexstring: str, options: dict[str, Any] | None = None, iswitness: bool | None = None) -> dict[str, Any]:
        """
        Add inputs to a transaction until it has enough in value to meet its out value.
        This will not modify existing inputs, and will add at most one change output to the outputs.
        No existing outputs will be modified unless “subtractFeeFromOutputs” is specified.
        Note that inputs which were signed may need to be resigned after completion since in/outputs have been added.
        The inputs added will not be signed, use signrawtransactionwithkey or signrawtransactionwithwallet for that.
        Note that all existing inputs must have their previous output transaction be in the wallet.
        Note that all inputs selected must be of standard form and P2SH scripts must be in the wallet using
        importaddress or addmultisigaddress (to calculate fees).
        You can see whether this is the case by checking the “solvable” field in the listunspent output.
        Only pay-to-pubkey, multisig, and P2SH versions thereof are currently supported for watch-only

        Parameters
        -------
        hexstring : str
            The hex string of the raw transaction

        options : dict
            For backward compatibility: passing in a true instead of an object will result in {“includeWatching”:true}
            “replaceable”: bool, (boolean, optional, default=fallback to wallet’s default) Marks this transaction
            as BIP125 replaceable. Allows this transaction to be replaced by a transaction with higher fees
            “conf_target”: n, (numeric, optional, default=fallback to wallet’s default) Confirmation target (in blocks)
             “estimate_mode”: “str”, (string, optional, default=UNSET) The fee estimate mode, must be one of:
             “UNSET” “ECONOMICAL” “CONSERVATIVE” }

        iswitness : bool
            Whether the transaction hex is a serialized witness transaction.
            If iswitness is not present, heuristic tests will be used in decoding

        Returns
        -------
        dict
            Object with hex, fee and changepos.
        """
        return self._client.call("fundrawtransaction", hexstring, options, iswitness)

    @overload
    def get_raw_transaction(self, txid: str) -> str: ...

    @overload
    def get_raw_transaction(
        self, txid: str, verbose: Literal[False] | None, blockhash: str | None = None
    ) -> str: ...

    @overload
    def get_raw_transaction(
        self, txid: str, verbose: Literal[True], blockhash: str | None = None
    ) -> dict[str, Any]: ...

    def get_raw_transaction(
        self, txid: str, verbose: bool | None = None, blockhash: str | None = None
    ) -> str | dict[str, Any]:
        """
        Return the raw transaction data. By default this function only works for mempool transactions.
        When called with a blockhash argument, getrawtransaction will return the transaction if the specified block
        is available and the transaction is found in that block. When called without a blockhash argument,
        getrawtransaction will return the transaction if it is in the mempool, or if -txindex is enabled and the
        transaction is in a block in the blockchain.
        Hint: Use gettransaction for wallet transactions.
        If verbose is ‘true’, returns an Object with information about ‘txid’.
        If verbose is ‘false’ or omitted, returns a string that is serialized, hex-encoded data for ‘txid’.

        Parameters
        -------
        txid : str
            The transaction id

        verbose : bool
            If false, return a string, otherwise return a json object

        blockhash : str
            The block in which to look for the transaction

        Returns
        -------
        str
            The serialized, hex-encoded data for ‘txid’
        dict
            Data for txid
        """
        return self._client.call("getrawtransaction", txid, verbose, blockhash)

    def get_transaction(self, txid: str) -> Transaction:
        """
        Returns a Transaction object for given txid.

        Parameters
        -------
        txid : str
            Transaction txid.

        Returns
        -------
        Transaction
            Transaction object
        """
        return Transaction.from_rpc(self._client.call("getrawtransaction", txid, True))

    def get_transactions(self, txids: list[str]) -> list[Transaction]:
        payloads = self._client.batch(
            *(RpcCall.of("getrawtransaction", txid, True) for txid in txids)
        )
        return [Transaction.from_rpc(payload) for payload in payloads]

    def get_transaction_summary(self, txid: str) -> TransactionSummary:
        transaction = self.get_transaction(txid)
        return TransactionSummary.of(transaction, self._spent_outputs_of(transaction))

    def _spent_outputs_of(self, transaction: Transaction) -> dict[OutPoint, Vout]:
        outpoints = transaction.spent_outpoints
        if not outpoints:
            return {}
        funding = self.get_transactions(sorted({each.txid for each in outpoints}))
        by_txid = {each.txid: each for each in funding}
        return {
            outpoint: by_txid[outpoint.txid].vouts[outpoint.vout]
            for outpoint in outpoints
            if outpoint.txid in by_txid
        }

    def join_psbts(self, txs: dict[str, Any]) -> None:
        """
        Joins multiple distinct PSBTs with different inputs and outputs into one PSBT with inputs and outputs from
        all of the PSBTs No input in any of the PSBTs can be in more than one of the PSBTs.

        Parameters
        -------
        txs : dict
            A json array of base64 strings of partially signed transactions.
        """
        self._client.call("joinpsbts", txs)

    def send_raw_transaction(self, hexstring: str, allowhighfees: bool | None = None) -> str:
        """
        Submits raw transaction (serialized, hex-encoded) to local node and network.
        Also see createrawtransaction and signrawtransactionwithkey calls.

        Parameters
        -------
        hexstring : str
            The hex string of the raw transaction.

        allowhighfees : bool
            Allow high fees.

        Returns
        -------
        str
            The transaction hash in hex
        """
        return self._client.call("sendrawtransaction", hexstring, allowhighfees)

    def sign_raw_transaction_with_key(self, hexstring: str, privkeys: dict[str, Any], prevtxs: dict[str, Any] | None = None, sighashtype: str | None = None) -> dict[str, Any]:
        """
        Sign inputs for raw transaction (serialized, hex-encoded). The second argument is an array of
        base58-encoded private keys that will be the only keys used to sign the transaction.
        The third optional argument (may be null) is an array of previous transaction outputs that this
        transaction depends on but may not yet be in the block chain.

        Parameters
        -------
        hexstring : str
            The transaction hex string

        privkeys : dict
            A json array of base58-encoded private keys for signing

        prevtxs : dict
            A json array of previous dependent transaction outputs

        sighashtype : str
            The signature hash type. Must be one of:
            “ALL” “NONE” “SINGLE” “ALL|ANYONECANPAY” “NONE|ANYONECANPAY” “SINGLE|ANYONECANPAY”

        Returns
        -------
        dict
            Object with hex-encoded raw transaction with signature(s) and errors.
        """
        return self._client.call("signrawtransactionwithkey", hexstring, privkeys, prevtxs, sighashtype)

    def test_mempool_accept(self, rawtxs: dict[str, Any], allowhighfees: bool | None = None) -> list[Any]:
        """
        Returns result of mempool acceptance tests indicating if raw transaction (serialized, hex-encoded)
        would be accepted by mempool. This checks if the transaction violates the consensus or policy rules.
        See sendrawtransaction call.

        Parameters
        -------
        rawtxs : dict
            An array of hex strings of raw transactions. Length must be one for now.

        allowhighfees : bool
            Allow high fees.

        Returns
        -------
        list
            Result of mempool acceptance tests indicating if raw transaction would be accepted by mempool.
        """
        return self._client.call("testmempoolaccept", rawtxs, allowhighfees)

    def utxo_update_psbt(self, psbt: str) -> None:
        """
        Updates a PSBT with witness UTXOs retrieved from the UTXO set or the mempool.

        Parameters
        -------
        psbt : str
            A base64 string of a PSBT.
        """
        self._client.call("utxoupdatepsbt", psbt)