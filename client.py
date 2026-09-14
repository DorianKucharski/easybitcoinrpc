from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from functools import cached_property
from types import TracebackType
from typing import Any, Iterable, Mapping, Sequence

import requests

from easybitcoinrpc.errors import (
    AuthenticationError,
    MalformedResponseError,
    RpcError,
    TransportError,
)

DEFAULT_TIMEOUT_SECONDS = 30.0
UNAUTHORIZED = 401


def _without_trailing_none(params: Sequence[Any]) -> tuple[Any, ...]:
    last_given = len(params)
    while last_given and params[last_given - 1] is None:
        last_given -= 1
    return tuple(params[:last_given])


@dataclass(frozen=True, slots=True)
class RpcCall:
    method: str
    params: tuple[Any, ...] = ()

    @classmethod
    def of(cls, method: str, *params: Any) -> RpcCall:
        return cls(method, _without_trailing_none(params))

    def as_payload(self, call_id: int) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": call_id,
            "method": self.method,
            "params": list(self.params),
        }


@dataclass(frozen=True, slots=True)
class NodeEndpoint:
    host: str = "127.0.0.1"
    port: int = 8332
    user: str = "user"
    password: str = "password"
    wallet: str | None = None

    def __post_init__(self) -> None:
        if not self.host:
            raise ValueError("host must not be empty")
        if not 0 < self.port < 65536:
            raise ValueError(f"port must be between 1 and 65535, got {self.port}")

    @property
    def url(self) -> str:
        origin = f"http://{self.host}:{self.port}"
        return f"{origin}/wallet/{self.wallet}" if self.wallet else origin

    def for_wallet(self, wallet: str | None) -> NodeEndpoint:
        return NodeEndpoint(self.host, self.port, self.user, self.password, wallet)


@dataclass(frozen=True)
class JsonRpcClient:
    endpoint: NodeEndpoint = field(default_factory=NodeEndpoint)
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    @cached_property
    def session(self) -> requests.Session:
        session = requests.Session()
        session.auth = (self.endpoint.user, self.endpoint.password)
        session.headers.update({"Content-Type": "application/json"})
        return session

    def call(self, method: str, *params: Any) -> Any:
        return self.batch(RpcCall.of(method, *params))[0]

    def batch(self, *calls: RpcCall) -> list[Any]:
        if not calls:
            return []
        payload = [call.as_payload(index) for index, call in enumerate(calls)]
        answers = self.__post(payload)
        return [_result_of(answer) for answer in _ordered_by_id(answers, len(calls))]

    def for_wallet(self, wallet: str | None) -> JsonRpcClient:
        return JsonRpcClient(self.endpoint.for_wallet(wallet), self.timeout_seconds)

    def close(self) -> None:
        if "session" in self.__dict__:
            self.session.close()

    def __enter__(self) -> JsonRpcClient:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def __post(self, payload: list[dict[str, Any]]) -> list[Mapping[str, Any]]:
        try:
            response = self.session.post(
                self.endpoint.url,
                data=json.dumps(payload, default=_encode_decimal),
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as failure:
            raise TransportError(f"cannot reach {self.endpoint.url}: {failure}") from failure

        if response.status_code == UNAUTHORIZED:
            raise AuthenticationError(
                f"{self.endpoint.url} rejected the credentials of user {self.endpoint.user!r}"
            )
        return _decoded_answers(response)


def _decoded_answers(response: requests.Response) -> list[Mapping[str, Any]]:
    try:
        decoded = json.loads(response.text, parse_float=Decimal)
    except ValueError as failure:
        raise MalformedResponseError(
            f"expected JSON, got HTTP {response.status_code} {response.reason}"
        ) from failure
    return decoded if isinstance(decoded, list) else [decoded]


def _ordered_by_id(answers: Iterable[Mapping[str, Any]], expected: int) -> list[Mapping[str, Any]]:
    by_id = {answer.get("id"): answer for answer in answers}
    unanswered = [call_id for call_id in range(expected) if call_id not in by_id]
    if unanswered:
        raise MalformedResponseError(f"no answer for call {unanswered[0]} of {expected}")
    return [by_id[call_id] for call_id in range(expected)]


def _result_of(answer: Mapping[str, Any]) -> Any:
    error = answer.get("error")
    if error is not None:
        raise RpcError.from_response(error)
    if "result" not in answer:
        raise MalformedResponseError("answer carries neither a result nor an error")
    return answer["result"]


def _encode_decimal(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"{type(value).__name__} is not JSON serializable")
