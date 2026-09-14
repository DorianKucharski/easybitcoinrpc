from __future__ import annotations

from typing import Any

from easybitcoinrpc.client import JsonRpcClient

class Control:
    def __init__(self, client: JsonRpcClient) -> None:
        self._client = client

    def get_memory_info(self, mode: str | None = None) -> dict[str, Any]:
        """
        Returns an object containing information about memory usage.

        Parameters
        -------
        mode : str
            determines what kind of information is returned.
            “stats” returns general statistics about memory usage in the daemon.
            “mallocinfo” returns an XML string describing low-level heap state
            default="stats"

        Returns
        -------
        dict
            Information about memory usage
        """
        return self._client.call("getmemoryinfo", mode)

    def get_rpc_info(self) -> dict[str, Any]:
        """
        Returns details of the RPC server.

        Returns
        -------
        dict
            Details of the RPC server
        """
        return self._client.call("getrpcinfo")

    def help(self, command: str | None = None) -> str:
        """
        List all commands, or get help for a specified command.

        Parameters
        -------
        command : str
            The command to get help on
            default=all commands

        Returns
        -------
        str
            The help text
        """
        return self._client.call("help", command)

    def logging(self, include: dict[str, Any] | None = None, exclude: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Gets and sets the logging configuration.
        When called without an argument, returns the list of categories with status that are currently being debug
        logged or not.
        When called with arguments, adds or removes categories from debug logging and return the lists above.
        The arguments are evaluated in order “include”, “exclude”.
        If an item is both included and excluded, it will thus end up being excluded.
        The valid logging categories are: net, tor, mempool, http, bench, zmq, db, rpc, estimatefee, addrman,
        selectcoins, reindex, cmpctblock, rand, prune, proxy, mempoolrej, libevent, coindb, qt, leveldb In addition,
        the following are available as category names with special meanings:
        “all”, “1” : represent all logging categories.
        “none”, “0” : even if other logging categories are specified, ignore all of them

        Parameters
        -------
        include : dict
            A json array of categories to add debug logging

        exclude : dict
            A json array of categories to remove debug logging

        Returns
        -------
        dict
            Dict where keys are the logging categories, and values indicates its status
        """
        return self._client.call("logging", include, exclude)

    def stop(self) -> None:
        """
        Stop Bitcoin server.
        """
        self._client.call("stop")

    def uptime(self) -> int:
        """
        Returns the total uptime of the server.

        Returns
        -------
        int
            The number of seconds that the server has been running
        """
        return self._client.call("uptime")