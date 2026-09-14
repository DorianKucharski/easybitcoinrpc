from __future__ import annotations

from typing import Any

from easybitcoinrpc.client import JsonRpcClient

class Generating:
    def __init__(self, client: JsonRpcClient) -> None:
        self._client = client

    def generate(self, nblocks: int, maxtries: int | None = None) -> list[Any]:
        """
        Mine up to nblocks blocks immediately (before the RPC call returns) to an address in the wallet.

        Parameters
        -------
        nblocks : int
            How many blocks are generated immediately.

        maxtries : int
            How many iterations to try.
            default=1000000

        Returns
        -------
        list
            hashes of blocks generated
        """
        return self._client.call("generate", nblocks, maxtries)

    def generate_to_address(self, nblocks: int, address: str, maxtries: int | None = None) -> list[Any]:
        """
        Mine blocks immediately to a specified address (before the RPC call returns)

        Parameters
        -------
        nblocks : int
            How many blocks are generated immediately.

        address : str
            The address to send the newly generated bitcoin to.

        maxtries : int
            How many iterations to try.
            default=1000000

        Returns
        -------
        list
            Hashes of blocks generated
        """
        return self._client.call("generatetoaddress", nblocks, address, maxtries)