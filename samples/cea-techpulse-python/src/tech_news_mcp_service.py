from __future__ import annotations

import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class TechNewsMcpService:
    """Client wrapper around the Tech News MCP server (stdio transport)."""

    def __init__(self, mcp_server_path: str):
        self._mcp_server_path = mcp_server_path
        self._session: ClientSession | None = None
        self._client_cm = None  
        self._session_cm = None
        self._is_connected = False
        self._lock = asyncio.Lock()



    async def connect(self) -> None:
        async with self._lock:
            if self._is_connected:
                return

            env = {**os.environ, "NEWS_API_KEY": os.environ.get("NEWS_API_KEY", "")}

            server_params = StdioServerParameters(
                command=sys.executable,
                args=[self._mcp_server_path],
                env=env,
            )

            client_cm = stdio_client(server_params)
            try:
                read_stream, write_stream = await client_cm.__aenter__()
            except Exception:
                raise

            session_cm = ClientSession(read_stream, write_stream)
            try:
                session = await session_cm.__aenter__()
                await session.initialize()
            except Exception:
                await session_cm.__aexit__(None, None, None)
                await client_cm.__aexit__(None, None, None)
                raise

            self._client_cm = client_cm
            self._session_cm = session_cm
            self._session = session
            self._is_connected = True

    async def disconnect(self) -> None:
        async with self._lock:
            if self._session_cm:
                await self._session_cm.__aexit__(None, None, None)
            if self._client_cm:
                await self._client_cm.__aexit__(None, None, None)
            self._session = None
            self._client_cm = None
            self._session_cm = None
            self._is_connected = False

    def is_service_connected(self) -> bool:
        return self._is_connected



    async def _call_tool(self, name: str, arguments: dict) -> str:
        if not self._session or not self._is_connected:
            raise RuntimeError("Tech News MCP client not connected")

        result = await self._session.call_tool(name, arguments)

        if result.content:
            text = getattr(result.content[0], "text", None) or "No data available"
            return text
        return "No results found"



    async def get_tech_news(
        self,
        category: str = "general",
        limit: int = 10,
    ) -> str:
        return await self._call_tool("get_tech_news", {"category": category, "limit": limit})

    async def search_tech_news(
        self,
        keyword: str,
        limit: int = 10,
        timeframe: str = "week",
    ) -> str:
        return await self._call_tool(
            "search_tech_news", {"keyword": keyword, "limit": limit, "timeframe": timeframe}
        )

    async def get_trending_tech(
        self,
        region: str = "us",
        limit: int = 10,
    ) -> str:
        return await self._call_tool("get_trending_tech", {"region": region, "limit": limit})

    async def get_company_news(
        self,
        company: str,
        limit: int = 8,
        timeframe: str = "week",
    ) -> str:
        return await self._call_tool(
            "get_company_news", {"company": company, "limit": limit, "timeframe": timeframe}
        )
