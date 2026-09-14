from __future__ import annotations

from typing import Any, Literal, overload

from easybitcoinrpc.client import JsonRpcClient, RpcCall
from easybitcoinrpc.errors import RpcError, VerbosityNotSupportedError
from easybitcoinrpc.models import Block, Transaction

def verbosity_argument(verbosity: int | bool | None) -> bool | int | None:
    """
    Translates a verbosity level into the argument getblock expects.

    Bitcoin Core older than 0.15 (and the forks derived from it) declare the second argument of
    getblock as a boolean verbose flag, so an integer is rejected with
    "-1: JSON value is not a boolean as expected". Newer versions accept a boolean as well as an
    integer, therefore levels 0 and 1 are always sent as booleans and only level 2 and above,
    which cannot be expressed as a boolean, is sent as an integer.

    Parameters
    -------
    verbosity : int or bool or None
        The requested verbosity level

    Returns
    -------
    bool or int or None
        The argument to pass to getblock
    """
    if verbosity is None or isinstance(verbosity, bool):
        return verbosity
    if verbosity == 0:
        return False
    if verbosity == 1:
        return True
    return verbosity


def _node_lacks_verbosity(error: RpcError, verbosity: int | bool | None) -> bool:
    requested_more_than_a_boolean = (
        not isinstance(verbosity, bool) and verbosity is not None and verbosity > 1
    )
    return requested_more_than_a_boolean and "boolean" in error.message


class Blockchain:
    def __init__(self, client: JsonRpcClient) -> None:
        self._client = client

    def resolve_block_hash(self, height_or_hash: int | str) -> str:
        if isinstance(height_or_hash, int):
            return self._client.call("getblockhash", height_or_hash)
        return height_or_hash

    def get_blocks(self, heights_or_hashes: list[int | str]) -> list[Block]:
        hashes = [self.resolve_block_hash(each) for each in heights_or_hashes]
        payloads = self._client.batch(
            *(RpcCall.of("getblock", block_hash, True) for block_hash in hashes)
        )
        return [Block.from_rpc(payload) for payload in payloads]

    def get_best_block_hash(self) -> str:
        """
        Returns the hash of the best (tip) block in the longest blockchain.

        Returns
        -------
        str
            The block hash, hex-encoded
        """
        return self._client.call("getbestblockhash")

    def get_best_block(self) -> Block:
        """
        Returns the object of the best (tip) block in the longest blockchain.

        Returns
        -------
        Block
            The block object
        """
        best_block_hash = self._client.call("getbestblockhash")
        return Block.from_rpc(self._client.call("getblock", best_block_hash, True))

    @overload
    def get_block(self, height_or_hash: int | str, verbosity: Literal[0]) -> str: ...

    @overload
    def get_block(
        self, height_or_hash: int | str, verbosity: Literal[1, 2] | None = 1
    ) -> Block: ...

    def get_block(self, height_or_hash: int | str, verbosity: int | None = 1) -> Block | str:
        """
        If verbosity is 1, returns an Block object.
        If verbosity is 2, returns an Block object with information about each transaction.

        Parameters
        -------
        height_or_hash : int | str
            Block height or hash

        verbosity : int
            1 for block object with txids, 2 for block object with transactions.

        Returns
        -------
        Block
            The block object
        """
        block_hash = self.resolve_block_hash(height_or_hash)
        try:
            block = self._client.call("getblock", block_hash, verbosity_argument(verbosity))
        except RpcError as error:
            if verbosity is not None and _node_lacks_verbosity(error, verbosity):
                raise VerbosityNotSupportedError(int(verbosity)) from error
            raise
        return block if verbosity == 0 else Block.from_rpc(block)

    def get_block_hex(self, height_or_hash: int | str) -> str:
        """
        Returns a string that is serialized, hex-encoded data for block.

        Parameters
        -------
        height_or_hash : int | str
            Block height or block hash

        Returns
        -------
        str
            The block data
        """
        return self._client.call("getblock", self.resolve_block_hash(height_or_hash), False)

    def get_blockchain_info(self) -> dict[str, Any]:
        """
        Returns an object containing various state info regarding blockchain processing.

        Returns
        -------
        dict
            Blockchain state info
            {
            "chain": "xxxx",              (string) current network name as defined in BIP70 (main, test, regtest)
            "blocks": xxxxxx,             (numeric) the current number of blocks processed in the server
            "headers": xxxxxx,            (numeric) the current number of headers we have validated
            "bestblockhash": "...",       (string) the hash of the currently best block
            "difficulty": xxxxxx,         (numeric) the current difficulty
            "mediantime": xxxxxx,         (numeric) median time for the current best block
            "verificationprogress": xxxx, (numeric) estimate of verification progress [0..1]
            "initialblockdownload": xxxx, (bool) (debug information) estimate of whether this node is in Initial Block
                                            Download mode.
            "chainwork": "xxxx"           (string) total amount of work in active chain, in hexadecimal
            "size_on_disk": xxxxxx,       (numeric) the estimated size of the block and undo files on disk
            "pruned": xx,                 (boolean) if the blocks are subject to pruning
            "pruneheight": xxxxxx,        (numeric) lowest-height complete block stored (only present if pruning is
                                            enabled)
            "automatic_pruning": xx,      (boolean) whether automatic pruning is enabled (only present if pruning is
                                            enabled)
            "prune_target_size": xxxxxx,  (numeric) the target size used by pruning (only present if automatic pruning
                                            is enabled)
            "softforks": [                (array) status of softforks in progress
             {
                "id": "xxxx",           (string) name of softfork
                "version": xx,          (numeric) block version
                "reject": {             (object) progress toward rejecting pre-softfork blocks
                   "status": xx,        (boolean) true if threshold reached
                },
             }, ...
            ],
            "bip9_softforks": {           (object) status of BIP9 softforks in progress
             "xxxx" : {                 (string) name of the softfork
                "status": "xxxx",       (string) one of "defined", "started", "locked_in", "active", "failed"
                "bit": xx,              (numeric) the bit (0-28) in the block version field used to signal this
                                            softfork (only for "started" status)
                "startTime": xx,        (numeric) the minimum median time past of a block at which the bit gains its
                                            meaning
                "timeout": xx,          (numeric) the median time past of a block at which the deployment is considered
                                            failed if not yet locked in
                "since": xx,            (numeric) height of the first block to which the status applies
                "statistics": {         (object) numeric statistics about BIP9 signalling for a softfork (only for
                                            "started" status)
                   "period": xx,        (numeric) the length in blocks of the BIP9 signalling period
                   "threshold": xx,     (numeric) the number of blocks with the version bit set required to activate
                                            the feature
                   "elapsed": xx,       (numeric) the number of blocks elapsed since the beginning of the current period
                   "count": xx,         (numeric) the number of blocks with the version bit set in the current period
                   "possible": xx       (boolean) returns false if there are not enough blocks left in this period to
                                            pass activation threshold
                }
             }
            }
            "warnings" : "...",           (string) any network and blockchain warnings.
            }
        """
        return self._client.call("getblockchaininfo")

    def get_block_count(self) -> int:
        """
        Returns the number of blocks in the longest blockchain.

        Returns
        -------
        int
            The current block count
        """
        return self._client.call("getblockcount")

    def get_block_hash(self, height: int) -> str:
        """
        Returns hash of block in best-block-chain at height provided.

        Parameters
        -------
        height : int
            The block height

        Returns
        -------
        str
            The block hash
        """
        return self._client.call("getblockhash", height)

    def get_block_header(self, height_or_hash: int | str, verbose: bool = True) -> dict[str, Any]:
        """
        If verbose is false, returns a string that is serialized, hex-encoded data for blockheader ‘hash’.
        If verbose is true, returns an Object with information about blockheader ‘hash’.

        Parameters
        -------
        height_or_hash : int | str
            The block height or hash

        verbose : int
            true for a dict object, false for the hex-encoded data

        Returns
        -------
        dict
            The block header
            {
            "hash" : "hash",       (string) the block hash (same as provided)
            "confirmations" : n,   (numeric) The number of confirmations, or -1 if the block is not on the main chain
            "height" : n,          (numeric) The block height or index
            "version" : n,         (numeric) The block version
            "versionHex" : "00000000", (string) The block version formatted in hexadecimal
            "merkleroot" : "xxxx", (string) The merkle root
            "time" : ttt,          (numeric) The block time in seconds since epoch (Jan 1 1970 GMT)
            "mediantime" : ttt,    (numeric) The median block time in seconds since epoch (Jan 1 1970 GMT)
            "nonce" : n,           (numeric) The nonce
            "bits" : "1d00ffff",   (string) The bits
            "difficulty" : x.xxx,  (numeric) The difficulty
            "chainwork" : "0000...1f3"     (string) Expected number of hashes required to produce the current chain
                                                (in hex)
            "nTx" : n,             (numeric) The number of transactions in the block.
            "previousblockhash" : "hash",  (string) The hash of the previous block
            "nextblockhash" : "hash",      (string) The hash of the next block
            }
        """
        if isinstance(height_or_hash, int):
            height_or_hash = self._client.call("getblockhash", height_or_hash)
        return self._client.call("getblockheader", height_or_hash, verbose)

    def get_block_stats(self, height_or_hash: int | str, stats: list[Any] | None = None) -> dict[str, Any]:
        """
        Compute per block statistics for a given window. All amounts are in satoshis.
        It won’t work for some heights with pruning.
        It won’t work without -txindex for utxo_size_inc, *fee or *feerate stats.

        Parameters
        -------
        height_or_hash : int | str
            The block height or hash

        stats : list
            Values to plot

        Returns
        -------
        dict
            The block stats
            {
            "avgfee": xxxxx,          (numeric) Average fee in the block
            "avgfeerate": xxxxx,      (numeric) Average feerate (in satoshis per virtual byte)
            "avgtxsize": xxxxx,       (numeric) Average transaction size
            "blockhash": xxxxx,       (string) The block hash (to check for potential reorgs)
            "feerate_percentiles": [  (array of numeric) Feerates at the 10th, 25th, 50th, 75th, and 90th
                                        percentile weight unit (in satoshis per virtual byte)
              "10th_percentile_feerate",      (numeric) The 10th percentile feerate
              "25th_percentile_feerate",      (numeric) The 25th percentile feerate
              "50th_percentile_feerate",      (numeric) The 50th percentile feerate
              "75th_percentile_feerate",      (numeric) The 75th percentile feerate
              "90th_percentile_feerate",      (numeric) The 90th percentile feerate
            ],
            "height": xxxxx,          (numeric) The height of the block
            "ins": xxxxx,             (numeric) The number of inputs (excluding coinbase)
            "maxfee": xxxxx,          (numeric) Maximum fee in the block
            "maxfeerate": xxxxx,      (numeric) Maximum feerate (in satoshis per virtual byte)
            "maxtxsize": xxxxx,       (numeric) Maximum transaction size
            "medianfee": xxxxx,       (numeric) Truncated median fee in the block
            "mediantime": xxxxx,      (numeric) The block median time past
            "mediantxsize": xxxxx,    (numeric) Truncated median transaction size
            "minfee": xxxxx,          (numeric) Minimum fee in the block
            "minfeerate": xxxxx,      (numeric) Minimum feerate (in satoshis per virtual byte)
            "mintxsize": xxxxx,       (numeric) Minimum transaction size
            "outs": xxxxx,            (numeric) The number of outputs
            "subsidy": xxxxx,         (numeric) The block subsidy
            "swtotal_size": xxxxx,    (numeric) Total size of all segwit transactions
            "swtotal_weight": xxxxx,  (numeric) Total weight of all segwit transactions divided by segwit scale factor
            "swtxs": xxxxx,           (numeric) The number of segwit transactions
            "time": xxxxx,            (numeric) The block time
            "total_out": xxxxx,       (numeric) Total amount in all outputs (excluding coinbase and thus reward
                                        [ie subsidy + totalfee])
            "total_size": xxxxx,      (numeric) Total size of all non-coinbase transactions
            "total_weight": xxxxx,    (numeric) Total weight of all non-coinbase transactions divided by segwit
                                        scale factor (4)
            "totalfee": xxxxx,        (numeric) The fee total
            "txs": xxxxx,             (numeric) The number of transactions (excluding coinbase)
            "utxo_increase": xxxxx,   (numeric) The increase/decrease in the number of unspent outputs
            "utxo_size_inc": xxxxx,   (numeric) The increase/decrease in size for the utxo index (not discounting
                                        op_return and similar)
            }
        """
        return self._client.call("getblockstats", height_or_hash, stats)

    def get_chain_tips(self) -> list[Any]:
        """
        Return information about all known tips in the block tree, including the main chain as well as orphaned
        branches.

        Returns
        -------
        list
            The block tree tips
            [{
            "height": xxxx,         (numeric) height of the chain tip
            "hash": "xxxx",         (string) block hash of the tip
            "branchlen": 0          (numeric) zero for main chain
            "status": "active"      (string) "active" for the main chain
            },
            {
            "height": xxxx,
            "hash": "xxxx",
            "branchlen": 1          (numeric) length of branch connecting the tip to the main chain
            "status": "xxxx"        (string) status of the chain (active, valid-fork, valid-headers, headers-only,
                                        invalid)
            }]
        """
        return self._client.call("getchaintips")

    def get_chain_tx_stats(self, nblocks: int | None = None, blockhash: str | None = None) -> dict[str, Any]:
        """
        Compute statistics about the total number and rate of transactions in the chain.

        Parameters
        -------
        nblocks : int
            Size of the window in number of blocks
            default=one month

        blockhash : str
            The hash of the block that ends the window.
            default=chain tip

        Returns
        -------
        dict
            Statistics
            {
            "time": xxxxx,                         (numeric) The timestamp for the final block in the window in UNIX
                                                        format.
            "txcount": xxxxx,                      (numeric) The total number of transactions in the chain up to that
                                                        point.
            "window_final_block_hash": "...",      (string) The hash of the final block in the window.
            "window_block_count": xxxxx,           (numeric) Size of the window in number of blocks.
            "window_tx_count": xxxxx,              (numeric) The number of transactions in the window. Only returned
                                                        if "window_block_count" is > 0.
            "window_interval": xxxxx,              (numeric) The elapsed time in the window in seconds. Only returned
                                                        if "window_block_count" is > 0.
            "txrate": x.xx,                        (numeric) The average rate of transactions per second in the window.
                                                        Only returned if "window_interval" is > 0.
            }
        """
        return self._client.call("getchaintxstats", nblocks, blockhash)

    def get_difficulty(self) -> int:
        """
        Returns the proof-of-work difficulty as a multiple of the minimum difficulty.

        Returns
        -------
        int
            The proof-of-work difficulty as a multiple of the minimum difficulty.
        """
        return self._client.call("getdifficulty")

    def get_mempool_ancestors(self, txid: str, verbose: bool = False) -> dict[str, Any]:
        """
        If txid is in the mempool, returns all in-mempool ancestors.

        Parameters
        -------
        txid : str
            The transaction id (must be in mempool)

        verbose : bool
            True for a json object, false for array of transaction ids.

        Returns
        -------
        dict
            Txid in-mempool ancestors
        """
        return self._client.call("getmempoolancestors", txid, verbose)

    def get_mempool_descendants(self, txid: str, verbose: bool | None = None) -> dict[str, Any]:
        """
        If txid is in the mempool, returns all in-mempool descendants.

        Parameters
        -------
        txid : str
            The transaction id (must be in mempool)

        verbose : bool
            True for a json object, false for array of transaction ids.

        Returns
        -------
        dict
            Txid in-mempool descendants
        """
        return self._client.call("getmempooldescendants", txid, verbose)

    def get_mempool_entry(self, txid: str) -> dict[str, Any]:
        """
        Returns mempool data for given transaction.

        Parameters
        -------
        txid : str
            The transaction id (must be in mempool)

        Returns
        -------
        dict
            Txid mempool data
        """
        return self._client.call("getmempoolentry", txid)

    def get_mempool_info(self) -> dict[str, Any]:
        """
        Returns details on the active state of the TX memory pool.

        Returns
        -------
        dict
            The mempool info
        """
        return self._client.call("getmempoolinfo")

    def get_raw_mempool(self, verbose: bool | None = None) -> dict[str, Any]:
        """
        Returns all transaction ids in memory pool as a json array of string transaction ids.
        Hint: use getmempoolentry to fetch a specific transaction from the mempool.

        Parameters
        -------
        verbose : bool
            True for a json object, false for array of transaction ids

        Returns
        -------
        dict
            All transaction ids in mempool
        """
        return self._client.call("getrawmempool", verbose)

    def get_tx_out(self, txid: str, n: int, include_mempool: bool | None = None) -> dict[str, Any]:
        """
        Returns details about an unspent transaction output.

        Parameters
        -------
        txid : str
            The transaction id

        n : int
            Vout number

        include_mempool : bool
            Whether to include the mempool. Note that an unspent output that is spent in the mempool won’t appear.

        Returns
        -------
        dict
            Details about an unspent transaction output
        """
        return self._client.call("gettxout", txid, n, include_mempool)

    def get_tx_out_proof(self, txids: list[Any], blockhash: str | None = None) -> str:
        """
        Returns a hex-encoded proof that “txid” was included in a block.

        NOTE: By default this function only works sometimes. This is when there is an unspent output in the utxo for
        this transaction. To make it always work, you need to maintain a transaction index, using the -txindex command
        line option or specify the block in which the transaction is included manually (by blockhash).

        Parameters
        -------
        txids : list
            A json array of txids to filter

        blockhash : str
            If specified, looks for txid in the block with this hash

        Returns
        -------
        str
            A string that is a serialized, hex-encoded data for the proof.
        """
        return self._client.call("gettxoutproof", txids, blockhash)

    def get_tx_out_set_info(self) -> dict[str, Any]:
        """
        Returns statistics about the unspent transaction output set. Note this call may take some time.

        Returns
        -------
        dict
            Statistics about the unspent transaction output set.
        """
        return self._client.call("gettxoutsetinfo")

    def precious_block(self, blockhash: str) -> None:
        """
        Treats a block as if it were received before others with the same work.
        A later preciousblock call can override the effect of an earlier one.
        The effects of preciousblock are not retained across restarts.

        Parameters
        -------
        blockhash : str
            the hash of the block to mark as precious

        """
        self._client.call("preciousblock", blockhash)

    def prune_blockchain(self, height: int) -> int:
        """
        Pruns up the blockchain of given height.

        Parameters
        -------
        height : int
            The block height to prune up to. May be set to a discrete height, or a unix timestamp
            to prune blocks whose block time is at least 2 hours older than the provided timestamp.

        Returns
        -------
        int
            Height of the last block pruned.
        """
        return self._client.call("pruneblockchain", height)

    def save_mempool(self) -> None:
        """
        Dumps the mempool to disk. It will fail until the previous dump is fully loaded.
        """
        self._client.call("savemempool")

    def scan_tx_out_set(self, action: str, scanobjects: list[Any]) -> dict[str, Any]:
        """
        XPERIMENTAL warning: this call may be removed or changed in future releases.
        Scans the unspent transaction output set for entries that match certain output descriptors.

        Parameters
        -------
        action : str
            The action to execute
            “start” for starting a scan
            “abort” for aborting the current scan (returns true when abort was successful)
            “status” for progress report (in %) of the current scan

        scanobjects: list
            Every scan object is either a string descriptor or an object

        Returns
        -------
        dict
            Unspents
        """
        return self._client.call("scantxoutset", action, scanobjects)

    def verify_chain(self, checklevel: int | None = None, nblocks: Any | None = None) -> bool:
        """
        Verifies blockchain database.

        Parameters
        -------
        checklevel : int
            How thorough the block verification is. range=0-4, default=3

        nblocks: int
            The number of blocks to check. 0=all, default=6

        Returns
        -------
        bool
            Verified or not
        """
        return self._client.call("verifychain", checklevel, nblocks)

    def verify_tx_out_proof(self, proof: str) -> list[Any]:
        """
        Verifies that a proof points to a transaction in a block, returning the transaction it commits to and throwing
        an RPC error if the block is not in our best chain.

        Parameters
        -------
        proof : str
            The hex-encoded proof generated by gettxoutproof

        Returns
        -------
        list
            List of txids, which the proof commits to, or empty array if the proof can not be validated
        """
        return self._client.call("verifytxoutproof", proof)
