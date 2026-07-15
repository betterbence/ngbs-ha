"""Async client for the local NGBS iCON JSON/TCP service."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any


class NgbsError(Exception):
    """Base NGBS exception."""


class NgbsConnectionError(NgbsError):
    """Raised when the controller cannot be reached."""


class NgbsProtocolError(NgbsError):
    """Raised for an invalid or rejected controller response."""


def _parse_response(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    sanitized = re.sub(
        r'(?<!\\)"(\s*:\s*)0{2,}(?=[,}\]\s]|$)',
        r'"\g<1>0',
        raw,
        flags=re.MULTILINE,
    )
    try:
        data = json.loads(sanitized)
    except json.JSONDecodeError as err:
        raise NgbsProtocolError(f"Invalid NGBS response: {raw}") from err
    if not isinstance(data, dict):
        raise NgbsProtocolError("NGBS response was not a JSON object")
    if data.get("ERR") == 1:
        raise NgbsProtocolError("NGBS rejected the request (incorrect SYSID?)")
    return data


class NgbsClient:
    """Client for the local service protocol on TCP port 7992."""

    def __init__(
        self,
        host: str,
        port: int = 7992,
        timeout: float = 5.0,
        sysid: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sysid = sysid
        self._lock = asyncio.Lock()

    async def request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send one JSON request over a short-lived TCP connection."""
        request_data = json.dumps(payload, separators=(",", ":")).encode()
        async with self._lock:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=self.timeout,
                )
            except (TimeoutError, OSError) as err:
                raise NgbsConnectionError(
                    f"Could not connect to {self.host}:{self.port}: {err}"
                ) from err

            try:
                writer.write(request_data)
                await writer.drain()
                if writer.can_write_eof():
                    writer.write_eof()
                response = await asyncio.wait_for(reader.read(), timeout=self.timeout)
            except (TimeoutError, OSError) as err:
                raise NgbsConnectionError(f"NGBS communication failed: {err}") from err
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass

        return _parse_response(response.decode("utf-8", errors="replace"))

    async def discover_sysid(self) -> str:
        """Discover and store the controller SYSID."""
        response = await self.request({"RELOAD": 6})
        sysid = response.get("SYSID")
        if not sysid:
            raise NgbsProtocolError("Controller did not return a SYSID")
        self.sysid = str(sysid)
        return self.sysid

    def _require_sysid(self) -> str:
        if not self.sysid:
            raise NgbsProtocolError("SYSID is not configured")
        return self.sysid

    async def get_state(self, include_config: bool = True) -> dict[str, Any]:
        """Get full controller state."""
        payload: dict[str, Any] = {"SYSID": self._require_sysid()}
        if include_config:
            payload["RELOAD"] = 3
        return await self.request(payload)

    async def _set_global(self, field: str, value: Any) -> None:
        await self.request({"SYSID": self._require_sysid(), field: value})

    async def _set_thermostat(self, thermostat_id: str, field: str, value: Any) -> None:
        await self.request(
            {"SYSID": self._require_sysid(), "DP": {thermostat_id: {field: value}}}
        )

    async def set_global_eco(self, enabled: bool) -> None:
        await self._set_global("CE", int(enabled))

    async def set_global_cooling(self, enabled: bool) -> None:
        await self._set_global("HC", int(enabled))

    async def set_thermostat_eco(self, thermostat_id: str, enabled: bool) -> None:
        await self._set_thermostat(thermostat_id, "CE", int(enabled))

    async def set_thermostat_cooling(self, thermostat_id: str, enabled: bool) -> None:
        await self._set_thermostat(thermostat_id, "HC", int(enabled))

    async def set_thermostat_target(self, thermostat_id: str, target: float) -> None:
        await self._set_thermostat(thermostat_id, "SP", target)

    async def set_parental_lock(self, thermostat_id: str, enabled: bool) -> None:
        await self._set_thermostat(thermostat_id, "PL", int(enabled))
