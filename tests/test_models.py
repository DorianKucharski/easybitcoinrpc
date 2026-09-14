from __future__ import annotations

import unittest
from decimal import Decimal

from easybitcoinrpc import RPC, ScriptPubKey, Transaction, TransactionSummary
from mock_node import (
    ALICE,
    BOB,
    CAROL,
    COINBASE_TRANSACTION,
    COINBASE_TXID,
    FUNDING_TRANSACTION,
    SPENDING_TRANSACTION,
    SPENDING_TXID,
    MockNode,
)


class TestScriptPubKey(unittest.TestCase):
    def test_a_single_address_field_is_normalised_to_a_tuple(self) -> None:
        script = ScriptPubKey.from_rpc({"address": ALICE})

        self.assertEqual(script.addresses, (ALICE,))

    def test_a_legacy_addresses_list_is_kept(self) -> None:
        script = ScriptPubKey.from_rpc({"addresses": [ALICE, BOB]})

        self.assertEqual(script.addresses, (ALICE, BOB))

    def test_a_script_without_addresses_yields_an_empty_tuple(self) -> None:
        self.assertEqual(ScriptPubKey.from_rpc({}).addresses, ())


class TestTransaction(unittest.TestCase):
    def test_a_coinbase_transaction_is_recognised(self) -> None:
        self.assertTrue(Transaction.from_rpc(COINBASE_TRANSACTION).is_coinbase)

    def test_a_spending_transaction_is_not_coinbase(self) -> None:
        self.assertFalse(Transaction.from_rpc(SPENDING_TRANSACTION).is_coinbase)

    def test_a_coinbase_transaction_spends_no_outpoint(self) -> None:
        self.assertEqual(Transaction.from_rpc(COINBASE_TRANSACTION).spent_outpoints, ())

    def test_spent_outpoints_name_the_funding_outputs(self) -> None:
        outpoints = Transaction.from_rpc(SPENDING_TRANSACTION).spent_outpoints

        self.assertEqual([each.vout for each in outpoints], [0, 1])

    def test_total_output_sums_the_vouts_as_decimal(self) -> None:
        total = Transaction.from_rpc(FUNDING_TRANSACTION).total_output

        self.assertIsInstance(total, Decimal)
        self.assertEqual(total, Decimal("3.0"))

    def test_occurred_at_is_timezone_aware(self) -> None:
        moment = Transaction.from_rpc(FUNDING_TRANSACTION).occurred_at

        self.assertIsNotNone(moment)
        self.assertIsNotNone(moment.tzinfo)

    def test_a_transaction_without_a_time_has_no_moment(self) -> None:
        self.assertIsNone(Transaction.from_rpc({"txid": "x"}).occurred_at)


class TestTransactionSummaryWithoutTheNode(unittest.TestCase):
    def test_a_coinbase_summary_has_no_inputs(self) -> None:
        summary = TransactionSummary.of(Transaction.from_rpc(COINBASE_TRANSACTION))

        self.assertEqual(summary.inputs, ())
        self.assertEqual(summary.total_output, Decimal("12.5"))

    def test_a_coinbase_summary_charges_no_fee(self) -> None:
        summary = TransactionSummary.of(Transaction.from_rpc(COINBASE_TRANSACTION))

        self.assertEqual(summary.fee, Decimal(0))

    def test_value_in_takes_the_price_as_an_argument(self) -> None:
        summary = TransactionSummary.of(Transaction.from_rpc(COINBASE_TRANSACTION))

        self.assertEqual(summary.value_in(Decimal("100")), Decimal("1250"))


class TestTransactionSummaryAgainstTheNode(unittest.TestCase):
    def setUp(self) -> None:
        self.node = MockNode().start()
        self.rpc = RPC(ip="127.0.0.1", port=self.node.port)
        self.addCleanup(self.rpc.close)
        self.addCleanup(self.node.stop)

    def test_inputs_are_resolved_from_the_funding_outputs(self) -> None:
        summary = self.rpc.transactions.get_transaction_summary(SPENDING_TXID)

        self.assertEqual([each.address for each in summary.inputs], [ALICE, BOB])
        self.assertEqual(summary.total_input, Decimal("3.0"))

    def test_outputs_carry_the_receiving_address(self) -> None:
        summary = self.rpc.transactions.get_transaction_summary(SPENDING_TXID)

        self.assertEqual([each.address for each in summary.outputs], [CAROL])

    def test_the_fee_is_the_difference_between_inputs_and_outputs(self) -> None:
        summary = self.rpc.transactions.get_transaction_summary(SPENDING_TXID)

        self.assertEqual(summary.fee, Decimal("0.1"))

    def test_resolving_the_inputs_does_not_query_once_per_input(self) -> None:
        self.rpc.transactions.get_transaction_summary(SPENDING_TXID)

        funding_lookups = self.node.methods_called().count("getrawtransaction")
        self.assertEqual(funding_lookups, 2)
        self.assertEqual(self.node.request_count, 2)

    def test_a_coinbase_summary_needs_no_funding_lookup(self) -> None:
        self.rpc.transactions.get_transaction_summary(COINBASE_TXID)

        self.assertEqual(self.node.request_count, 1)

    def test_get_transactions_fetches_them_in_one_request(self) -> None:
        fetched = self.rpc.transactions.get_transactions([SPENDING_TXID, COINBASE_TXID])

        self.assertEqual([each.txid for each in fetched], [SPENDING_TXID, COINBASE_TXID])
        self.assertEqual(self.node.request_count, 1)


if __name__ == "__main__":
    unittest.main()
