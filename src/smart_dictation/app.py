import asyncio
import structlog

from smart_dictation import clipboard, hotkeys
from smart_dictation.audio import (
    get_device_info,
    get_sound_devices,
    record_audio,
    get_default_device,
)
from smart_dictation.config import WhisperImpl, cfg
from smart_dictation.local_whisper import WhisperCppTranscriber, to_whisper_ndarray

log = structlog.get_logger(__name__)

match (cfg.whisper_impl):
    case WhisperImpl.cpp:
        transcribe = WhisperCppTranscriber()
    case WhisperImpl.openai:
        raise NotImplementedError("API not implemented")
    case WhisperImpl.realtime:
        raise NotImplementedError("Realtime not implemented")
    case _:
        raise ValueError(f"Invalid whisper implementation: {cfg.whisper_impl}")


async def dictate(key_released):

    device_info = get_device_info(cfg.input_device_index)
    await log.ainfo("Recording, device: %s", device_info["name"])
    wave = await record_audio(
        key_released, convert=to_whisper_ndarray, device=cfg.input_device_index
    )
    text = await transcribe(wave)
    await log.ainfo("Pasting: %s", text)
    await clipboard.paste_text(text)


async def start_listening():
    if cfg.input_device_index is None:
        await log.ainfo("No input device specified, using default")
        idx, name = get_default_device()
        print(f"Current device id: {idx} - {name}")
        list_sound_devices()

    transcribe.preload()
    await hotkeys.listen_for_hotkeys({cfg.hotkey: dictate})


def list_sound_devices():
    """Print the list of input sound devices."""
    devices = get_sound_devices()
    print("Available input devices:")
    for device_id, device_name in devices:
        print(f"Input Device id: {device_id} - {device_name}")


def main():
    asyncio.run(start_listening())


if __name__ == "__main__":
    main()
