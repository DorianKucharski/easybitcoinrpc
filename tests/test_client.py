from __future__ import annotations

import unittest
from decimal import Decimal

from easybitcoinrpc import RPC, AuthenticationError, RpcCall
from easybitcoinrpc.client import NodeEndpoint, _without_trailing_none
from easybitcoinrpc.errors import (
    InsufficientFundsError,
    InvalidParameterError,
    MethodNotFoundError,
    RpcError,
    RpcErrorCode,
    WalletNotFoundError,
)
from mock_node import BLOCK_HASH, BLOCK_HEIGHT, MockNode


class TestNodeEndpoint(unittest.TestCase):
    def test_url_without_a_wallet(self) -> None:
        self.assertEqual(NodeEndpoint("10.0.0.1", 8332).url, "http://10.0.0.1:8332")

    def test_url_with_a_wallet(self) -> None:
        endpoint = NodeEndpoint("10.0.0.1", 8332, wallet="savings")

        self.assertEqual(endpoint.url, "http://10.0.0.1:8332/wallet/savings")

    def test_empty_host_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            NodeEndpoint(host="")

    def test_port_out_of_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as raised:
            NodeEndpoint(port=70000)

        self.assertIn("70000", str(raised.exception))


class TestTrailingNoneRemoval(unittest.TestCase):
    def test_trailing_none_is_dropped(self) -> None:
        self.assertEqual(_without_trailing_none(["txid", True, None]), ("txid", True))

    def test_none_between_values_is_kept(self) -> None:
        self.assertEqual(_without_trailing_none([None, 1]), (None, 1))

    def test_all_none_becomes_empty(self) -> None:
        self.assertEqual(_without_trailing_none([None, None]), ())


class TestErrorMapping(unittest.TestCase):
    def test_an_unknown_method_maps_to_method_not_found(self) -> None:
        error = RpcError.from_response({"code": RpcErrorCode.METHOD_NOT_FOUND, "message": "x"})

        self.assertIsInstance(error, MethodNotFoundError)

    def test_a_missing_wallet_maps_to_wallet_not_found(self) -> None:
        error = RpcError.from_response({"code": RpcErrorCode.WALLET_NOT_FOUND, "message": "x"})

        self.assertIsInstance(error, WalletNotFoundError)

    def test_insufficient_funds_maps_to_its_own_error(self) -> None:
        error = RpcError.from_response(
            {"code": RpcErrorCode.WALLET_INSUFFICIENT_FUNDS, "message": "x"}
        )

        self.assertIsInstance(error, InsufficientFundsError)

    def test_a_bad_parameter_maps_to_invalid_parameter(self) -> None:
        error = RpcError.from_response({"code": RpcErrorCode.INVALID_PARAMETER, "message": "x"})

        self.assertIsInstance(error, InvalidParameterError)

    def test_an_unmapped_code_stays_the_base_error(self) -> None:
        error = RpcError.from_response({"code": -1, "message": "boom"})

        self.assertIs(type(error), RpcError)
        self.assertEqual(error.code, -1)
        self.assertEqual(error.message, "boom")


class ClientTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.node = MockNode().start()
        self.rpc = RPC(ip="127.0.0.1", port=self.node.port)
        self.addCleanup(self.rpc.close)
        self.addCleanup(self.node.stop)


class TestJsonRpcClient(ClientTestCase):
    def test_call_returns_the_result(self) -> None:
        self.assertEqual(self.rpc.client.call("getbestblockhash"), BLOCK_HASH)

    def test_call_drops_a_trailing_none_argument(self) -> None:
        self.rpc.client.call("getblockhash", BLOCK_HEIGHT, None)

        self.assertEqual(self.node.arguments_of("getblockhash"), [BLOCK_HEIGHT])

    def test_batch_preserves_the_order_of_the_calls(self) -> None:
        results = self.rpc.client.batch(
            RpcCall.of("getblockcount"),
            RpcCall.of("getbestblockhash"),
            RpcCall.of("getblockhash", BLOCK_HEIGHT),
        )

        self.assertEqual(results, [BLOCK_HEIGHT, BLOCK_HASH, BLOCK_HASH])

    def test_batch_of_many_calls_costs_one_request(self) -> None:
        self.rpc.client.batch(*(RpcCall.of("getblockcount") for _ in range(5)))

        self.assertEqual(self.node.request_count, 1)

    def test_empty_batch_asks_the_node_nothing(self) -> None:
        self.assertEqual(self.rpc.client.batch(), [])
        self.assertEqual(self.node.request_count, 0)

    def test_amounts_arrive_as_decimal(self) -> None:
        difficulty = self.rpc.blockchain.get_block(BLOCK_HASH).difficulty

        self.assertIsInstance(difficulty, Decimal)
        self.assertEqual(difficulty, Decimal("1.5"))

    def test_a_rejected_call_carries_code_and_message(self) -> None:
        with self.assertRaises(RpcError) as raised:
            self.rpc.client.call("getblockhash", "not-a-height")

        self.assertEqual(raised.exception.code, -1)
        self.assertIn("integer", raised.exception.message)

    def test_rpc_for_wallet_targets_the_wallet_endpoint(self) -> None:
        savings = self.rpc.for_wallet("savings")

        self.assertTrue(savings.client.endpoint.url.endswith("/wallet/savings"))


class TestRejectedCredentials(unittest.TestCase):
    def test_a_401_is_reported_as_an_authentication_error(self) -> None:
        node = MockNode(unauthorized=True).start()
        self.addCleanup(node.stop)
        rpc = RPC(ip="127.0.0.1", port=node.port, user="wrong")
        self.addCleanup(rpc.close)

        with self.assertRaises(AuthenticationError) as raised:
            rpc.client.call("getbestblockhash")

        self.assertIn("wrong", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
