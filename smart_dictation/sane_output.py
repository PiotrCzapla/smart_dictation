import sys
import asyncio
import pyperclip
from AppKit import NSPasteboard  # type: ignore
from typing import Callable, Coroutine
from pynput.keyboard import Key, HotKey, GlobalHotKeys, Controller
import structlog

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
        with self as listner_thread:
            await asyncio.gather(*[h.in_main_loop() for h in self._hotkeys])


async def save_clipboard():
    """Saves the current clipboard content."""
    paste_board = NSPasteboard.generalPasteboard()
    old_clipboard = {}
    try:
        types = paste_board.types()
        for t in types:
            data = paste_board.dataForType_(t)
            old_clipboard[t] = data
    except Exception as e:
        print(f"Error saving clipboard: {e}")
    return old_clipboard


async def restore_clipboard(old_clipboard: dict, after: float = 0.5):
    """
    Restores the clipboard content after a delay.

    Args:
        after (float): Delay in seconds before restoring.
    """
    if old_clipboard:
        await asyncio.sleep(after)
        paste_board = NSPasteboard.generalPasteboard()
        paste_board.clearContents()
        try:
            for t, data in old_clipboard.items():
                paste_board.setData_forType_(data, t)
        except Exception as e:
            log.warning("Error restoring clipboard: %s", str(e))


async def trigger_paste_with_pynput():
    """Trigger cmd+v to paste, it is visible faster than using osascript"""
    command_key = Key.cmd if sys.platform == "darwin" else Key.ctrl
    keyboard = Controller()
    keyboard.press(command_key)
    keyboard.press("v")
    await asyncio.sleep(0.01)
    keyboard.release("v")
    keyboard.release(command_key)


async def paste_text(text):
    original_clipboard_content = await save_clipboard()
    try:
        pyperclip.copy(text)
        await trigger_paste_with_pynput()
    except Exception as e:
        log.warning("Error encoding text with pyperclip: %s", str(e))
    finally:
        await restore_clipboard(original_clipboard_content)
