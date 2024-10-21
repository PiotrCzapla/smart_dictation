from smart_dictation import sane_output
from smart_dictation.audio import get_sound_devices, record_audio, get_device_info
from smart_dictation.local_whisper import to_whisper_ndarray
import structlog
from smart_dictation.config import cfg, WhisperImpl
from smart_dictation.local_whisper import WhisperCppTranscriber

log = structlog.get_logger(__name__)

match (cfg.whisper_impl):
    case WhisperImpl.cpp:
        transcribe = WhisperCppTranscriber()
    case WhisperImpl.api:
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
    await sane_output.paste_text(text)


async def start_listening():
    transcribe.preload()
    global_hotkeys = sane_output.AsyncGlobalHotKeys({cfg.hotkey: dictate})
    await global_hotkeys.run_forever()


def list_sound_devices():
    """Print the list of input sound devices."""
    devices = get_sound_devices()
    for device_id, device_name in devices:
        print(f"Input Device id {device_id} - {device_name}")
