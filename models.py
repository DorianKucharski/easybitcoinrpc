from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping, Sequence

SATOSHIS_PER_BITCOIN = Decimal(100_000_000)
NO_SPENT_OUTPUTS: Mapping["OutPoint", "Vout"] = MappingProxyType({})


def _amount(value: Any) -> Decimal:
    return Decimal(str(value)) if value is not None else Decimal(0)


def _addresses_of(script_pubkey: Mapping[str, Any]) -> tuple[str, ...]:
    listed = script_pubkey.get("addresses")
    if listed:
        return tuple(listed)
    single = script_pubkey.get("address")
    return (single,) if single else ()


@dataclass(frozen=True, slots=True)
class ScriptPubKey:
    asm: str
    hex: str
    type: str
    addresses: tuple[str, ...]
    required_signatures: int | None

    @classmethod
    def from_rpc(cls, payload: Mapping[str, Any]) -> ScriptPubKey:
        return cls(
            asm=payload.get("asm", ""),
            hex=payload.get("hex", ""),
            type=payload.get("type", ""),
            addresses=_addresses_of(payload),
            required_signatures=payload.get("reqSigs"),
        )


@dataclass(frozen=True, slots=True)
class ScriptSig:
    asm: str
    hex: str

    @classmethod
    def from_rpc(cls, payload: Mapping[str, Any]) -> ScriptSig:
        return cls(asm=payload.get("asm", ""), hex=payload.get("hex", ""))


@dataclass(frozen=True, slots=True)
class Vin:
    sequence: int
    txid: str | None = None
    vout: int | None = None
    script_sig: ScriptSig | None = None
    witness: tuple[str, ...] = ()
    coinbase: str | None = None

    @classmethod
    def from_rpc(cls, payload: Mapping[str, Any]) -> Vin:
        script_sig = payload.get("scriptSig")
        return cls(
            sequence=payload.get("sequence", 0),
            txid=payload.get("txid"),
            vout=payload.get("vout"),
            script_sig=ScriptSig.from_rpc(script_sig) if script_sig else None,
            witness=tuple(payload.get("txinwitness", ())),
            coinbase=payload.get("coinbase"),
        )

    @property
    def is_coinbase(self) -> bool:
        return self.coinbase is not None

    @property
    def is_segwit(self) -> bool:
        return bool(self.witness)


@dataclass(frozen=True, slots=True)
class Vout:
    value: Decimal
    n: int
    script_pubkey: ScriptPubKey

    @classmethod
    def from_rpc(cls, payload: Mapping[str, Any]) -> Vout:
        return cls(
            value=_amount(payload.get("value")),
            n=payload.get("n", 0),
            script_pubkey=ScriptPubKey.from_rpc(payload.get("scriptPubKey", {})),
        )

    @property
    def satoshis(self) -> int:
        return int(self.value * SATOSHIS_PER_BITCOIN)


@dataclass(frozen=True, slots=True)
class OutPoint:
    txid: str
    vout: int


@dataclass(frozen=True, slots=True)
class AddressAmount:
    address: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class Transaction:
    txid: str
    hash: str
    version: int
    size: int
    vsize: int
    weight: int
    locktime: int
    vins: tuple[Vin, ...]
    vouts: tuple[Vout, ...]
    hex: str | None = None
    block_hash: str | None = None
    confirmations: int | None = None
    time: int | None = None
    block_time: int | None = None

    @classmethod
    def from_rpc(cls, payload: Mapping[str, Any]) -> Transaction:
        return cls(
            txid=payload.get("txid", ""),
            hash=payload.get("hash", payload.get("txid", "")),
            version=payload.get("version", 0),
            size=payload.get("size", 0),
            vsize=payload.get("vsize", payload.get("size", 0)),
            weight=payload.get("weight", 0),
            locktime=payload.get("locktime", 0),
            vins=tuple(Vin.from_rpc(vin) for vin in payload.get("vin", ())),
            vouts=tuple(Vout.from_rpc(vout) for vout in payload.get("vout", ())),
            hex=payload.get("hex"),
            block_hash=payload.get("blockhash"),
            confirmations=payload.get("confirmations"),
            time=payload.get("time"),
            block_time=payload.get("blocktime"),
        )

    @property
    def is_coinbase(self) -> bool:
        return any(vin.is_coinbase for vin in self.vins)

    @property
    def is_segwit(self) -> bool:
        return any(vin.is_segwit for vin in self.vins)

    @property
    def spent_outpoints(self) -> tuple[OutPoint, ...]:
        return tuple(
            OutPoint(vin.txid, vin.vout)
            for vin in self.vins
            if vin.txid is not None and vin.vout is not None
        )

    @property
    def total_output(self) -> Decimal:
        return sum((vout.value for vout in self.vouts), Decimal(0))

    @property
    def occurred_at(self) -> datetime | None:
        moment = self.time if self.time is not None else self.block_time
        return datetime.fromtimestamp(moment, tz=timezone.utc) if moment else None


@dataclass(frozen=True, slots=True)
class Block:
    hash: str
    confirmations: int
    height: int
    version: int
    version_hex: str
    merkle_root: str
    time: int
    median_time: int
    nonce: int
    bits: str
    difficulty: Decimal
    chainwork: str
    transaction_count: int
    transaction_ids: tuple[str, ...]
    size: int = 0
    stripped_size: int = 0
    weight: int = 0
    previous_block_hash: str | None = None
    next_block_hash: str | None = None
    transactions: tuple[Transaction, ...] = ()

    @classmethod
    def from_rpc(cls, payload: Mapping[str, Any]) -> Block:
        listed = payload.get("tx", ())
        carries_full_transactions = bool(listed) and isinstance(listed[0], Mapping)
        return cls(
            hash=payload.get("hash", ""),
            confirmations=payload.get("confirmations", 0),
            height=payload.get("height", 0),
            version=payload.get("version", 0),
            version_hex=payload.get("versionHex", ""),
            merkle_root=payload.get("merkleroot", ""),
            time=payload.get("time", 0),
            median_time=payload.get("mediantime", 0),
            nonce=payload.get("nonce", 0),
            bits=payload.get("bits", ""),
            difficulty=_amount(payload.get("difficulty")),
            chainwork=payload.get("chainwork", ""),
            transaction_count=payload.get("nTx", len(listed)),
            transaction_ids=(
                tuple(entry["txid"] for entry in listed)
                if carries_full_transactions
                else tuple(listed)
            ),
            size=payload.get("size", 0),
            stripped_size=payload.get("strippedsize", 0),
            weight=payload.get("weight", 0),
            previous_block_hash=payload.get("previousblockhash"),
            next_block_hash=payload.get("nextblockhash"),
            transactions=(
                tuple(Transaction.from_rpc(entry) for entry in listed)
                if carries_full_transactions
                else ()
            ),
        )

    @property
    def mined_at(self) -> datetime:
        return datetime.fromtimestamp(self.time, tz=timezone.utc)


def _shared_between(addresses: Sequence[str], value: Decimal) -> tuple[AddressAmount, ...]:
    if not addresses:
        return ()
    share = value / len(addresses)
    return tuple(AddressAmount(address, share) for address in addresses)


@dataclass(frozen=True, slots=True)
class TransactionSummary:
    transaction: Transaction
    inputs: tuple[AddressAmount, ...]
    outputs: tuple[AddressAmount, ...]

    @classmethod
    def of(
        cls,
        transaction: Transaction,
        spent_outputs: Mapping[OutPoint, Vout] = NO_SPENT_OUTPUTS,
    ) -> TransactionSummary:
        inputs = tuple(
            entry
            for outpoint in transaction.spent_outpoints
            if outpoint in spent_outputs
            for entry in _shared_between(
                spent_outputs[outpoint].script_pubkey.addresses,
                spent_outputs[outpoint].value,
            )
        )
        outputs = tuple(
            entry
            for vout in transaction.vouts
            for entry in _shared_between(vout.script_pubkey.addresses, vout.value)
        )
        return cls(transaction=transaction, inputs=inputs, outputs=outputs)

    @property
    def total_input(self) -> Decimal:
        return sum((entry.amount for entry in self.inputs), Decimal(0))

    @property
    def total_output(self) -> Decimal:
        return sum((entry.amount for entry in self.outputs), Decimal(0))

    @property
    def fee(self) -> Decimal:
        return Decimal(0) if self.transaction.is_coinbase else self.total_input - self.total_output

    def value_in(self, price_per_bitcoin: Decimal) -> Decimal:
        return self.total_output * price_per_bitcoin
