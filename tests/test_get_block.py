"""
Regression tests for issue #1, where get_block raised
"-1: JSON value is not a boolean as expected" against nodes whose getblock takes a boolean.
"""

import pytest
from bitcoinrpc.authproxy import JSONRPCException

from easybitcoinrpc import RPC, Block
from easybitcoinrpc.blockchain import verbosity_argument
from mock_node import BLOCK_HASH, BLOCK_HEIGHT, BLOCK_HEX, LEGACY, MODERN, TXIDS, MockNode


@pytest.fixture(params=[LEGACY, MODERN])
def node(request):
    node = MockNode(request.param).start()
    yield node
    node.stop()


@pytest.fixture
def rpc(node):
    return RPC(ip="127.0.0.1", port=node.port, user="user", password="password")


@pytest.mark.parametrize("verbosity", [0, 1, 2])
def test_verbosity_argument_avoids_integers_a_boolean_can_express(verbosity):
    assert verbosity_argument(verbosity) == [False, True, 2][verbosity]


@pytest.mark.parametrize("verbosity", [None, True, False])
def test_verbosity_argument_passes_through_what_needs_no_translation(verbosity):
    assert verbosity_argument(verbosity) is verbosity


def test_get_block_by_height(node, rpc):
    """The call from issue #1, which has to work on old and new nodes alike."""
    block = rpc.blockchain.get_block(height_or_hash=BLOCK_HEIGHT)

    assert isinstance(block, Block)
    assert block.get_height() == BLOCK_HEIGHT
    assert node.arguments_of("getblockhash") == [BLOCK_HEIGHT]


def test_get_block_by_hash(node, rpc):
    assert rpc.blockchain.get_block(BLOCK_HASH).get_hash() == BLOCK_HASH


@pytest.mark.parametrize("verbosity, sent", [(1, True), (0, False)])
def test_get_block_sends_a_boolean_for_the_levels_a_boolean_can_express(node, rpc, verbosity, sent):
    rpc.blockchain.get_block(BLOCK_HASH, verbosity)

    assert node.arguments_of("getblock") == [BLOCK_HASH, sent]


def test_get_block_with_verbosity_0_returns_the_hex(node, rpc):
    assert rpc.blockchain.get_block(BLOCK_HASH, 0) == BLOCK_HEX


def test_get_block_hex(node, rpc):
    assert rpc.blockchain.get_block_hex(BLOCK_HEIGHT) == BLOCK_HEX
    assert node.arguments_of("getblock") == [BLOCK_HASH, False]


def test_get_best_block(node, rpc):
    assert rpc.blockchain.get_best_block().get_hash() == BLOCK_HASH


def test_verbosity_2_is_still_sent_as_an_integer(rpc, node):
    if node.mode == LEGACY:
        pytest.skip("verbosity 2 needs Bitcoin Core 0.15 or newer")

    block = rpc.blockchain.get_block(BLOCK_HEIGHT, 2)

    assert node.arguments_of("getblock") == [BLOCK_HASH, 2]
    assert [transaction.get_txid() for transaction in block.get_transactions()] == TXIDS


def test_verbosity_2_on_a_node_without_support_explains_itself(rpc, node):
    if node.mode == MODERN:
        pytest.skip("this node supports verbosity 2")

    with pytest.raises(JSONRPCException) as raised:
        rpc.blockchain.get_block(BLOCK_HEIGHT, 2)

    assert "0.15" in str(raised.value)
    assert "boolean" not in str(raised.value)
