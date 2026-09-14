from __future__ import annotations

import unittest

from easybitcoinrpc import RPC, Block, VerbosityNotSupportedError
from easybitcoinrpc.blockchain import verbosity_argument
from mock_node import BLOCK_HASH, BLOCK_HEIGHT, BLOCK_HEX, LEGACY, MODERN, MockNode


class TestVerbosityArgument(unittest.TestCase):
    def test_verbosity_zero_becomes_a_boolean(self) -> None:
        self.assertIs(verbosity_argument(0), False)

    def test_verbosity_one_becomes_a_boolean(self) -> None:
        self.assertIs(verbosity_argument(1), True)

    def test_verbosity_two_stays_an_integer(self) -> None:
        self.assertEqual(verbosity_argument(2), 2)

    def test_none_passes_through(self) -> None:
        self.assertIsNone(verbosity_argument(None))

    def test_boolean_passes_through(self) -> None:
        self.assertIs(verbosity_argument(True), True)


class BlockchainTestCase(unittest.TestCase):
    mode = MODERN

    def setUp(self) -> None:
        self.node = MockNode(self.mode).start()
        self.rpc = RPC(ip="127.0.0.1", port=self.node.port)
        self.addCleanup(self.rpc.close)
        self.addCleanup(self.node.stop)


class TestGetBlockOnModernNode(BlockchainTestCase):
    mode = MODERN

    def test_get_block_by_height_returns_a_block(self) -> None:
        block = self.rpc.blockchain.get_block(BLOCK_HEIGHT)

        self.assertIsInstance(block, Block)
        self.assertEqual(block.height, BLOCK_HEIGHT)
        self.assertEqual(self.node.arguments_of("getblockhash"), [BLOCK_HEIGHT])

    def test_get_block_by_hash_skips_the_height_lookup(self) -> None:
        self.rpc.blockchain.get_block(BLOCK_HASH)

        self.assertNotIn("getblockhash", self.node.methods_called())

    def test_get_block_sends_a_boolean_for_verbosity_one(self) -> None:
        self.rpc.blockchain.get_block(BLOCK_HASH, 1)

        self.assertEqual(self.node.arguments_of("getblock"), [BLOCK_HASH, True])

    def test_get_block_with_verbosity_zero_returns_the_hex(self) -> None:
        self.assertEqual(self.rpc.blockchain.get_block(BLOCK_HASH, 0), BLOCK_HEX)
        self.assertEqual(self.node.arguments_of("getblock"), [BLOCK_HASH, False])

    def test_get_block_with_verbosity_two_carries_transactions(self) -> None:
        block = self.rpc.blockchain.get_block(BLOCK_HEIGHT, 2)

        self.assertEqual(self.node.arguments_of("getblock"), [BLOCK_HASH, 2])
        self.assertEqual(len(block.transactions), block.transaction_count)
        self.assertEqual(
            [each.txid for each in block.transactions], list(block.transaction_ids)
        )

    def test_get_block_hex_sends_a_boolean(self) -> None:
        self.assertEqual(self.rpc.blockchain.get_block_hex(BLOCK_HEIGHT), BLOCK_HEX)
        self.assertEqual(self.node.arguments_of("getblock"), [BLOCK_HASH, False])

    def test_get_best_block_returns_a_block(self) -> None:
        self.assertEqual(self.rpc.blockchain.get_best_block().hash, BLOCK_HASH)

    def test_get_blocks_uses_a_single_request(self) -> None:
        blocks = self.rpc.blockchain.get_blocks([BLOCK_HASH, BLOCK_HASH, BLOCK_HASH])

        self.assertEqual(len(blocks), 3)
        self.assertEqual(self.node.request_count, 1)


class TestGetBlockOnNodeTakingABooleanVerboseFlag(BlockchainTestCase):
    mode = LEGACY

    def test_get_block_by_height_works(self) -> None:
        self.assertEqual(self.rpc.blockchain.get_block(BLOCK_HEIGHT).height, BLOCK_HEIGHT)

    def test_get_block_hex_works(self) -> None:
        self.assertEqual(self.rpc.blockchain.get_block_hex(BLOCK_HEIGHT), BLOCK_HEX)

    def test_verbosity_two_reports_the_node_is_too_old(self) -> None:
        with self.assertRaises(VerbosityNotSupportedError) as raised:
            self.rpc.blockchain.get_block(BLOCK_HEIGHT, 2)

        self.assertIn("0.15", str(raised.exception))
        self.assertNotIn("boolean", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
