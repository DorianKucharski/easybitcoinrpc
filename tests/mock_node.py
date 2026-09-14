from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Mapping

LEGACY = "legacy"
MODERN = "modern"

BLOCK_HEIGHT = 488271
BLOCK_HASH = "00000000000000000024fb37364cbf81fd49cc2d51c09c75c35433c3a1945d04"
BLOCK_HEX = "0100beef"

FUNDING_TXID = "aa" * 32
SPENDING_TXID = "bb" * 32
COINBASE_TXID = "cc" * 32

ALICE = "bc1qalice"
BOB = "bc1qbob"
CAROL = "bc1qcarol"


class NodeRejection(Exception):
    pass


def _get_bool(value: Any) -> bool:
    if type(value) is not bool:
        raise NodeRejection("JSON value is not a boolean as expected")
    return value


def _get_int(value: Any) -> int:
    if type(value) is not int:
        raise NodeRejection("JSON value is not an integer as expected")
    return value


def _script_pub_key(address: str) -> dict[str, Any]:
    return {"asm": "OP_DUP", "hex": "76a914", "type": "witness_v0_keyhash", "address": address}


def _vout(index: int, value: float, address: str) -> dict[str, Any]:
    return {"value": value, "n": index, "scriptPubKey": _script_pub_key(address)}


FUNDING_TRANSACTION = {
    "txid": FUNDING_TXID,
    "hash": FUNDING_TXID,
    "version": 2,
    "size": 200,
    "vsize": 150,
    "weight": 600,
    "locktime": 0,
    "vin": [{"txid": "dd" * 32, "vout": 0, "sequence": 4294967295}],
    "vout": [_vout(0, 1.0, ALICE), _vout(1, 2.0, BOB)],
    "time": 1508000000,
    "blockhash": BLOCK_HASH,
}

SPENDING_TRANSACTION = {
    "txid": SPENDING_TXID,
    "hash": SPENDING_TXID,
    "version": 2,
    "size": 200,
    "vsize": 150,
    "weight": 600,
    "locktime": 0,
    "vin": [
        {"txid": FUNDING_TXID, "vout": 0, "sequence": 4294967295},
        {"txid": FUNDING_TXID, "vout": 1, "sequence": 4294967295},
    ],
    "vout": [_vout(0, 2.9, CAROL)],
    "time": 1508000600,
    "blockhash": BLOCK_HASH,
}

COINBASE_TRANSACTION = {
    "txid": COINBASE_TXID,
    "hash": COINBASE_TXID,
    "version": 2,
    "size": 200,
    "vsize": 150,
    "weight": 600,
    "locktime": 0,
    "vin": [{"coinbase": "03abcdef", "sequence": 4294967295}],
    "vout": [_vout(0, 12.5, ALICE)],
    "time": 1508000000,
    "blockhash": BLOCK_HASH,
}

TRANSACTIONS_BY_TXID = {
    FUNDING_TXID: FUNDING_TRANSACTION,
    SPENDING_TXID: SPENDING_TRANSACTION,
    COINBASE_TXID: COINBASE_TRANSACTION,
}

TXIDS = (COINBASE_TXID, SPENDING_TXID)


def _block(verbosity: int) -> dict[str, Any]:
    listed: list[Any] = (
        [TRANSACTIONS_BY_TXID[txid] for txid in TXIDS] if verbosity >= 2 else list(TXIDS)
    )
    return {
        "hash": BLOCK_HASH,
        "confirmations": 12,
        "height": BLOCK_HEIGHT,
        "version": 536870912,
        "versionHex": "20000000",
        "merkleroot": "ee" * 32,
        "time": 1508000000,
        "mediantime": 1507999000,
        "nonce": 1234567,
        "bits": "1d00ffff",
        "difficulty": 1.5,
        "chainwork": "ff" * 32,
        "nTx": len(TXIDS),
        "size": 1000,
        "strippedsize": 900,
        "weight": 4000,
        "previousblockhash": "11" * 32,
        "tx": listed,
    }


class MockNode:
    def __init__(self, mode: str = MODERN, unauthorized: bool = False) -> None:
        self.mode = mode
        self.unauthorized = unauthorized
        self.calls: list[tuple[str, list[Any]]] = []
        self.request_count = 0
        self.__server: HTTPServer | None = None

    def start(self) -> MockNode:
        self.__server = HTTPServer(("127.0.0.1", 0), self.__handler())
        threading.Thread(target=self.__server.serve_forever, daemon=True).start()
        return self

    def stop(self) -> None:
        if self.__server is not None:
            self.__server.shutdown()
            self.__server.server_close()

    @property
    def port(self) -> int:
        assert self.__server is not None
        return self.__server.server_address[1]

    def methods_called(self) -> list[str]:
        return [method for method, _ in self.calls]

    def arguments_of(self, method: str) -> list[Any]:
        return [params for name, params in self.calls if name == method][-1]

    def getbestblockhash(self, params: list[Any]) -> str:
        return BLOCK_HASH

    def getblockhash(self, params: list[Any]) -> str:
        _get_int(params[0])
        return BLOCK_HASH

    def getrawtransaction(self, params: list[Any]) -> Mapping[str, Any]:
        return TRANSACTIONS_BY_TXID[params[0]]

    def getblockcount(self, params: list[Any]) -> int:
        return BLOCK_HEIGHT

    def getblock(self, params: list[Any]) -> Any:
        if len(params) < 2 or params[1] is None:
            verbosity = 1
        elif self.mode == LEGACY:
            verbosity = 1 if _get_bool(params[1]) else 0
        elif type(params[1]) is bool:
            verbosity = 1 if params[1] else 0
        else:
            verbosity = _get_int(params[1])
        if verbosity >= 2 and self.mode == LEGACY:
            raise NodeRejection("JSON value is not a boolean as expected")
        return BLOCK_HEX if verbosity == 0 else _block(verbosity)

    def __answer(self, call: Mapping[str, Any]) -> dict[str, Any]:
        self.calls.append((call["method"], call["params"]))
        try:
            return {"result": getattr(self, call["method"])(call["params"]), "error": None,
                    "id": call["id"]}
        except NodeRejection as rejection:
            return {"result": None, "error": {"code": -1, "message": str(rejection)},
                    "id": call["id"]}
        except KeyError as missing:
            return {"result": None, "error": {"code": -5, "message": f"no entry {missing}"},
                    "id": call["id"]}

    def __handler(self) -> type[BaseHTTPRequestHandler]:
        node = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                pass

            def do_POST(self) -> None:
                node.request_count += 1
                if node.unauthorized:
                    self.send_response(401)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                calls = body if isinstance(body, list) else [body]
                answers = [node._MockNode__answer(call) for call in calls]
                payload = json.dumps(answers if isinstance(body, list) else answers[0]).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        return Handler
