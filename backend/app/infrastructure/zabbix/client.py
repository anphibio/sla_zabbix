from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib import request


Transport = Callable[[str, dict[str, object]], dict[str, object]]


class ZabbixApiError(Exception):
    pass


class ZabbixClient:
    def __init__(
        self,
        url: str,
        token: str,
        transport: Transport | None = None,
    ) -> None:
        self.url = url
        self.token = token
        self._transport = transport or self._default_transport

    def build_request(
        self,
        method: str,
        params: dict[str, object],
    ) -> dict[str, object]:
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
            "auth": self.token,
        }

    def call(self, method: str, params: dict[str, object]) -> object:
        payload = self.build_request(method=method, params=params)
        response = self._transport(self.url, payload)

        if "error" in response:
            raise ZabbixApiError(str(response["error"]))
        if "result" not in response:
            raise ZabbixApiError("missing_result")

        return response["result"]

    def get_hostgroup_by_name(self, name: str) -> dict[str, str] | None:
        result = self.call(
            "hostgroup.get",
            {
                "output": ["groupid", "name"],
                "filter": {"name": [name]},
            },
        )
        groups = [group for group in result if isinstance(group, dict)]

        if not groups:
            return None

        group = groups[0]
        return {
            "groupid": str(group["groupid"]),
            "name": str(group["name"]),
        }

    def get_trigger_events(
        self,
        *,
        time_from: int,
        time_till: int,
        tag_name: str | None = None,
        tag_value: str | None = None,
        groupids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, object] = {
            "output": [
                "eventid",
                "clock",
                "name",
                "severity",
                "r_eventid",
                "value",
            ],
            "source": 0,
            "object": 0,
            "value": 1,
            "problem_time_from": time_from,
            "problem_time_till": time_till,
            "sortfield": ["clock", "eventid"],
            "sortorder": "ASC",
            "selectTags": "extend",
        }

        if tag_name is not None and tag_value is not None:
            params["evaltype"] = 0
            params["tags"] = [
                {
                    "tag": tag_name,
                    "value": tag_value,
                    "operator": 1,
                }
            ]

        if groupids:
            params["groupids"] = groupids

        result = self.call("event.get", params)
        return [event for event in result if isinstance(event, dict)]

    def get_events_by_ids(self, eventids: list[str]) -> list[dict[str, Any]]:
        if not eventids:
            return []

        result = self.call(
            "event.get",
            {
                "output": ["eventid", "clock", "value"],
                "eventids": eventids,
                "source": 0,
                "object": 0,
            },
        )
        return [event for event in result if isinstance(event, dict)]

    @staticmethod
    def _default_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json-rpc"}
        http_request = request.Request(url, data=body, headers=headers, method="POST")

        with request.urlopen(http_request, timeout=30) as response:
            raw_response = response.read().decode("utf-8")

        parsed_response = json.loads(raw_response)

        if not isinstance(parsed_response, dict):
            raise ZabbixApiError("invalid_response")

        return parsed_response
