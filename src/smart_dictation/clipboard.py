import asyncio
import sys

import pyperclip
import structlog
from pynput.keyboard import Controller, Key

log = structlog.get_logger(__name__)


async def save_clipboard():
    """Saves the current clipboard content, generic text version."""
    return {"text": pyperclip.paste()}


async def restore_clipboard(old_clipboard: dict, after: float = 0.5):
    """Restores the clipboard content, generic text version."""
    await asyncio.sleep(after)
    pyperclip.copy(old_clipboard["text"])


if sys.platform == "darwin":
    from AppKit import NSPasteboard  # type: ignore

    async def save_clipboard_mac():
        """Saves the current clipboard content. MacOS supports all content types."""
        paste_board = NSPasteboard.generalPasteboard()
        try:
            old_clipboard = {
                t: paste_board.dataForType_(t) for t in paste_board.types()
            }
        except Exception as e:
            log.warning("Error saving clipboard: %s", str(e))
        return old_clipboard

    async def restore_clipboard_mac(old_clipboard: dict, after: float = 0.5):
        """Restores the clipboard content after a delay. MacOS supports all content types."""
        if old_clipboard:
            await asyncio.sleep(after)
            paste_board = NSPasteboard.generalPasteboard()
            paste_board.clearContents()
            try:
                for t, data in old_clipboard.items():
                    paste_board.setData_forType_(data, t)
            except Exception as e:
                log.warning("Error restoring clipboard: %s", str(e))

    save_clipboard = save_clipboard_mac
    restore_clipboard = restore_clipboard_mac


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
    """Paste text, restoring the original clipboard content."""
    original_clipboard_content = await save_clipboard()
    try:
        pyperclip.copy(text)
        await trigger_paste_with_pynput()
    except Exception as e:
        log.warning("Error encoding text with pyperclip: %s", str(e))
    finally:
        await restore_clipboard(original_clipboard_content)
