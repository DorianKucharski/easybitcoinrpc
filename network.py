from __future__ import annotations

from typing import Any

from easybitcoinrpc.client import JsonRpcClient

class Network:
    def __init__(self, client: JsonRpcClient) -> None:
        self._client = client

    def add_node(self, node: str, command: str) -> None:
        """
        Attempts to add or remove a node from the addnode list. Or try a connection to a node once.
        Nodes added using addnode (or -connect) are protected from DoS disconnection and are not required to be
        full nodes/support SegWit as other outbound peers are (though such peers will not be synced from)

        Parameters
        -------
        node : str
            The node (see getpeerinfo for nodes)

        command : st
            ‘add’ to add a node to the list, ‘remove’ to remove a node from the list, ‘onetry’ to try a connection to
            the node once
        """
        self._client.call("addnode", node, command)

    def clear_banned(self) -> None:
        """
        Clear all banned IPs.
        """
        self._client.call("clearbanned")

    def disconnect_node(self, address: str | None = None, nodeid: int | None = None) -> None:
        """
        Immediately disconnects from the specified peer node.
        Strictly one out of ‘address’ and ‘nodeid’ can be provided to identify the node.
        To disconnect by nodeid, either set ‘address’ to the empty string, or call using the named ‘nodeid’ argument
        only.

        Parameters
        -------
        address : str
            The IP address/port of the node.

        nodeid : int
            The node ID (see getpeerinfo for node IDs)
        """
        self._client.call("disconnectnode", address, nodeid)

    def get_added_node_info(self, node: str | None = None) -> dict[str, Any]:
        """
        Returns information about the given added node, or all added nodes (note that onetry addnodes are not listed
        here)

        Parameters
        -------
        node : str
            If provided, return information about this specific node, otherwise all nodes are returned.

        Returns
        -------
        dict
             Information about the given added node.
        """
        return self._client.call("getaddednodeinfo", node)

    def get_connection_count(self) -> int:
        """
        Returns the number of connections to other nodes.

        Returns
        -------
        int
            The connection count
        """
        return self._client.call("getconnectioncount")

    def get_net_totals(self) -> dict[str, Any]:
        """
        Returns information about network traffic, including bytes in, bytes out, and current time.

        Returns
        -------
        dict
            Information about network traffic.
        """
        return self._client.call("getnettotals")

    def get_network_info(self) -> dict[str, Any]:
        """
        Returns an object containing various state info regarding P2P networking.

        Returns
        -------
        dict
            Object containing various state info regarding P2P networking.
        """
        return self._client.call("getnetworkinfo")

    def get_node_addresses(self, count: int | None = None) -> list[Any]:
        """
        Return known addresses which can potentially be used to find new nodes in the network.

        Parameters
        -------
        count : int
            How many addresses to return. Limited to the smaller of 2500 or 23% of all known addresses.

        Returns
        -------
        list
            Addresses which can potentially be used to find new nodes in the network.
        """
        return self._client.call("getnodeaddresses", count)

    def get_peer_info(self) -> list[Any]:
        """
        Returns data about each connected network node as a json array of objects.

        Returns
        -------
        list
            Data about each connected network node as a json array of objects.
        """
        return self._client.call("getpeerinfo")

    def list_banned(self) -> list[Any]:
        """
        List all banned IPs/Subnets.

        Returns
        -------
        list
            List of all banned IPs/Subnets.
        """
        return self._client.call("listbanned")

    def ping(self) -> None:
        """
        Requests that a ping be sent to all other nodes, to measure ping time.
        Results provided in getpeerinfo, pingtime and pingwait fields are decimal seconds.
        Ping command is handled in queue with all other commands, so it measures processing backlog, not just network
        ping.
        """
        self._client.call("ping")

    def set_ban(self, subnet: str, command: str, bantime: int | None = None, absolute: bool | None = None) -> None:
        """
        Attempts to add or remove an IP/Subnet from the banned list.

        Parameters
        -------
        subnet : str
            The IP/Subnet (see getpeerinfo for nodes IP) with an optional netmask (default is /32 = single IP)

        command : str
            ‘add’ to add an IP/Subnet to the list,
            ‘remove’ to remove an IP/Subnet from the list

        bantime : int
            time in seconds how long (or until when if [absolute] is set) the IP is banned (0 or empty means
            using the default time of 24h which can also be overwritten by the -bantime startup argument)

        absolute : bool
            If set, the bantime must be an absolute timestamp in seconds since epoch (Jan 1 1970 GMT)
        """
        self._client.call("setban", subnet, command, bantime, absolute)

    def set_network_active(self, state: bool) -> None:
        """
        Disable/enable all p2p network activity.

        Parameters
        -------
        state : bool
            true to enable networking, false to disable
        """
        self._client.call("setnetworkactive", state)