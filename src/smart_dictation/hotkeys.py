import asyncio
import sys
from typing import Callable, Coroutine

import pyperclip
import structlog
from pynput.keyboard import Controller, GlobalHotKeys, HotKey, Key

log = structlog.get_logger(__name__)


class StopTask(RuntimeError):
    pass


class AsyncHotKey(HotKey):
    def __init__(
        self,
        keys,
        async_call: Callable[[asyncio.Event], Coroutine],
    ):
        super().__init__(keys, self.__on_activate)
        self._on_activate_single_call = async_call
        self._activated = False
        self._released_event = asyncio.Event()
        self._pressed_event = asyncio.Event()
        self._pressed_event.clear()
        self._released_event.set()
        self._loop = asyncio.get_event_loop()

    def __on_activate(self):
        if not self._activated:
            self._activated = True
            self._loop.call_soon_threadsafe(
                lambda: (self._pressed_event.set(), self._released_event.clear())
            )

    def __on_deactivate(self):
        if self._activated:
            self._activated = False
            self._loop.call_soon_threadsafe(
                lambda: (self._pressed_event.clear(), self._released_event.set())
            )

    def press(self, key):
        super().press(key)

    def release(self, key):
        super().release(key)
        if self._state != self._keys and self._activated:  # type: ignore
            self.__on_deactivate()

    async def in_main_loop(self):
        while True:
            try:
                await self._pressed_event.wait()
                self._released_event.clear()
                await self._on_activate_single_call(self._released_event)
            except StopTask as e:
                log.info("Cancelled: %s", str(e))


class AsyncGlobalHotKeys(GlobalHotKeys):
    def __init__(
        self,
        hotkeys: dict[str, Callable[[asyncio.Event], Coroutine]],
        *args,
        **kwargs,
    ):
        super().__init__({}, *args, **kwargs)
        self._loop = asyncio.get_event_loop()
        self._hotkeys = [
            AsyncHotKey([self.canonical(key) for key in HotKey.parse(key)], value)
            for key, value in hotkeys.items()
        ]

    async def run_forever(self):
        """Start the global hotkeys listener asynchronously."""
        with self:
            await asyncio.gather(*[h.in_main_loop() for h in self._hotkeys])


async def listen_for_hotkeys(hotkeys: dict[str, Callable[[asyncio.Event], Coroutine]]):
    """Listen for hotkeys asynchronously."""
    global_hotkeys = AsyncGlobalHotKeys(hotkeys)
    await global_hotkeys.run_forever()
