"""Lightweight single-process STDIO server for the six CRC-LNM tools."""

from __future__ import annotations

import asyncio
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from crc_lnm_mcp.runtime import RuntimeProvider
from crc_lnm_mcp.tools import register_all


def _build_mcp() -> Any:
    """Construct FastMCP only when protocol operations actually begin."""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        warnings.showwarning = lambda *args, **kwargs: None
        import fastmcp.server.auth.providers.jwt  # noqa: F401
        from fastmcp import FastMCP

        instance = FastMCP(
            "crc-lnm-medical-agent",
            instructions="CRC-LNM single-model research-assistance tools over STDIO.",
        )
        register_all(instance, RuntimeProvider())
    return instance


class _LazyMCP:
    """Delay FastMCP's optional HTTP-stack imports until server use."""

    def __init__(self) -> None:
        self._instance: Any | None = None

    def get(self) -> Any:
        if self._instance is None:
            self._instance = _build_mcp()
        return self._instance

    def __getattr__(self, name: str) -> Any:
        return getattr(self.get(), name)


mcp = _LazyMCP()


def run() -> None:
    """Run the six-tool server directly over STDIO without CLI parsing."""

    async def serve() -> None:
        # NumPy is an approved dependency of the feature layer.  Its Windows
        # extension DLLs must be initialized before FastMCP/Docket starts
        # worker threads; Torch, model classes, preprocessors, and weights all
        # remain deferred until the first prediction call.
        import numpy  # noqa: F401

        loop = asyncio.get_running_loop()
        # Docket's in-memory cancellation pubsub polls through
        # asyncio.to_thread().  A single reusable executor thread prevents a
        # Windows thread-start/GIL deadlock when Torch imports native modules
        # during the first prediction, without preloading inference code.
        executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="crc-lnm-cancellation",
        )
        loop.set_default_executor(executor)
        try:
            await mcp.get().run_async(transport="stdio", show_banner=False)
        finally:
            executor.shutdown(wait=True, cancel_futures=True)

    asyncio.run(serve())


__all__ = ["mcp", "run"]
