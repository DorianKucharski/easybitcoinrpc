from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from types import TracebackType

from easybitcoinrpc.blockchain import Blockchain
from easybitcoinrpc.client import DEFAULT_TIMEOUT_SECONDS, JsonRpcClient, NodeEndpoint
from easybitcoinrpc.control import Control
from easybitcoinrpc.generating import Generating
from easybitcoinrpc.mining import Mining
from easybitcoinrpc.network import Network
from easybitcoinrpc.raw_transactions import RawTransactions
from easybitcoinrpc.util import Util
from easybitcoinrpc.wallet import Wallet


@dataclass(frozen=True)
class RPC:
    ip: str = "127.0.0.1"
    port: int = 8332
    user: str = "user"
    password: str = "password"
    wallet_name: str | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    @cached_property
    def client(self) -> JsonRpcClient:
        endpoint = NodeEndpoint(self.ip, int(self.port), self.user, self.password, self.wallet_name)
        return JsonRpcClient(endpoint, self.timeout_seconds)

    @cached_property
    def blockchain(self) -> Blockchain:
        return Blockchain(self.client)

    @cached_property
    def control(self) -> Control:
        return Control(self.client)

    @cached_property
    def generating(self) -> Generating:
        return Generating(self.client)

    @cached_property
    def mining(self) -> Mining:
        return Mining(self.client)

    @cached_property
    def network(self) -> Network:
        return Network(self.client)

    @cached_property
    def transactions(self) -> RawTransactions:
        return RawTransactions(self.client)

    @cached_property
    def util(self) -> Util:
        return Util(self.client)

    @cached_property
    def wallet(self) -> Wallet:
        return Wallet(self.client)

    def for_wallet(self, wallet_name: str | None) -> RPC:
        return RPC(self.ip, self.port, self.user, self.password, wallet_name, self.timeout_seconds)

    def close(self) -> None:
        if "client" in self.__dict__:
            self.client.close()

    def __enter__(self) -> RPC:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
