from __future__ import annotations

from enum import IntEnum
from typing import Any, Mapping


class RpcErrorCode(IntEnum):
    MISC = -1
    TYPE = -3
    WALLET = -4
    INVALID_ADDRESS_OR_KEY = -5
    WALLET_INSUFFICIENT_FUNDS = -6
    OUT_OF_MEMORY = -7
    INVALID_PARAMETER = -8
    CLIENT_NOT_CONNECTED = -9
    CLIENT_IN_INITIAL_DOWNLOAD = -10
    WALLET_INVALID_LABEL_NAME = -11
    WALLET_KEYPOOL_RAN_OUT = -12
    WALLET_UNLOCK_NEEDED = -13
    WALLET_PASSPHRASE_INCORRECT = -14
    WALLET_WRONG_ENC_STATE = -15
    WALLET_ENCRYPTION_FAILED = -16
    WALLET_ALREADY_UNLOCKED = -17
    WALLET_NOT_FOUND = -18
    WALLET_NOT_SPECIFIED = -19
    DATABASE = -20
    DESERIALIZATION = -22
    VERIFY = -25
    VERIFY_REJECTED = -26
    VERIFY_ALREADY_IN_CHAIN = -27
    IN_WARMUP = -28
    METHOD_DEPRECATED = -32
    PARSE = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL = -32603


class EasyBitcoinRpcError(Exception):
    pass


class TransportError(EasyBitcoinRpcError):
    pass


class AuthenticationError(TransportError):
    pass


class MalformedResponseError(TransportError):
    pass


class RpcError(EasyBitcoinRpcError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message

    @classmethod
    def from_response(cls, error: Mapping[str, Any]) -> RpcError:
        code = int(error.get("code", RpcErrorCode.MISC))
        message = str(error.get("message", ""))
        return _ERROR_CLASSES_BY_CODE.get(code, cls)(code, message)


class MethodNotFoundError(RpcError):
    pass


class InvalidParameterError(RpcError):
    pass


class WalletError(RpcError):
    pass


class WalletNotFoundError(WalletError):
    pass


class WalletPassphraseIncorrectError(WalletError):
    pass


class WalletUnlockNeededError(WalletError):
    pass


class InsufficientFundsError(WalletError):
    pass


class NodeWarmingUpError(RpcError):
    pass


class VerbosityNotSupportedError(RpcError):
    def __init__(self, verbosity: int) -> None:
        super().__init__(
            RpcErrorCode.MISC,
            f"verbosity {verbosity} requires Bitcoin Core 0.15 or newer, "
            f"this node only supports verbosity 0 and 1",
        )


_ERROR_CLASSES_BY_CODE: dict[int, type[RpcError]] = {
    RpcErrorCode.METHOD_NOT_FOUND: MethodNotFoundError,
    RpcErrorCode.INVALID_PARAMETER: InvalidParameterError,
    RpcErrorCode.INVALID_PARAMS: InvalidParameterError,
    RpcErrorCode.TYPE: InvalidParameterError,
    RpcErrorCode.WALLET: WalletError,
    RpcErrorCode.WALLET_NOT_FOUND: WalletNotFoundError,
    RpcErrorCode.WALLET_NOT_SPECIFIED: WalletNotFoundError,
    RpcErrorCode.WALLET_PASSPHRASE_INCORRECT: WalletPassphraseIncorrectError,
    RpcErrorCode.WALLET_UNLOCK_NEEDED: WalletUnlockNeededError,
    RpcErrorCode.WALLET_INSUFFICIENT_FUNDS: InsufficientFundsError,
    RpcErrorCode.IN_WARMUP: NodeWarmingUpError,
}
