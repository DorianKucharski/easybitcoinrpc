"""
A stand-in for bitcoind that reproduces the argument checking of Bitcoin Core.

Bitcoin Core rejects an argument of the wrong type from UniValue, which the RPC server reports
as code -1 with the message of the underlying error. Nodes older than 0.15, and the forks derived
from them, declare the second argument of getblock as a boolean verbose flag, so an integer is
rejected; 0.15 and newer accept a boolean as well as an integer verbosity. LEGACY and MODERN
emulate the two behaviours.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

LEGACY = "legacy"
MODERN = "modern"

BLOCK_HEIGHT = 488271
BLOCK_HASH = "00000000000000000024fb37364cbf81fd49cc2d51c09c75c35433c3a1945d04"
BLOCK_HEX = "0100beef"
TXIDS = ["aa" * 32, "bb" * 32]


class NodeError(Exception):
    """A rejected argument, which Bitcoin Core reports as code -1."""


def get_bool(value):
    if type(value) != bool:
        raise NodeError("JSON value is not a boolean as expected")
    return value


def get_int(value):
    if type(value) != int:
        raise NodeError("JSON value is not an integer as expected")
    return value


def block(verbosity):
    result = {"hash": BLOCK_HASH, "height": BLOCK_HEIGHT, "nTx": len(TXIDS)}
    if verbosity >= 2:
        result["tx"] = [{"txid": txid, "vin": [], "vout": []} for txid in TXIDS]
    else:
        result["tx"] = list(TXIDS)
    return result


class MockNode:
    """An HTTP server answering the handful of calls the tests exercise."""

    def __init__(self, mode):
        self.mode = mode
        self.calls = []
        self.__server = None

    def start(self):
        self.__server = HTTPServer(("127.0.0.1", 0), self.__handler())
        threading.Thread(target=self.__server.serve_forever, daemon=True).start()
        return self

    def stop(self):
        self.__server.shutdown()
        self.__server.server_close()

    @property
    def port(self):
        return self.__server.server_address[1]

    def arguments_of(self, method):
        """The arguments of the last call to the given method, without the method name."""
        return [call[1] for call in self.calls if call[0] == method][-1]

    def getbestblockhash(self, params):
        return BLOCK_HASH

    def getblockhash(self, params):
        get_int(params[0])
        return BLOCK_HASH

    def getrawtransaction(self, params):
        return {"txid": params[0], "vin": [], "vout": []}

    def getblock(self, params):
        if len(params) < 2 or params[1] is None:
            verbosity = 1
        elif self.mode == LEGACY:
            verbosity = 1 if get_bool(params[1]) else 0
        elif type(params[1]) == bool:
            verbosity = 1 if params[1] else 0
        else:
            verbosity = get_int(params[1])
        if verbosity >= 2 and self.mode == LEGACY:
            raise NodeError("JSON value is not a boolean as expected")
        return BLOCK_HEX if verbosity == 0 else block(verbosity)

    def __dispatch(self, call):
        self.calls.append((call["method"], call["params"]))
        try:
            result = getattr(self, call["method"])(call["params"])
            return {"result": result, "error": None, "id": call["id"]}
        except NodeError as error:
            return {"result": None, "error": {"code": -1, "message": str(error)}, "id": call["id"]}

    def __handler(self):
        node = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                calls = body if type(body) == list else [body]
                answers = [node._MockNode__dispatch(call) for call in calls]
                payload = json.dumps(answers if type(body) == list else answers[0]).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        return Handler
