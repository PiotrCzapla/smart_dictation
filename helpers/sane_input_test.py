import asyncio
import enum
import smart_dictation.sane_output as sane_output
import pyaudio
import numpy as np

import wave
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def to_wave(samples, *, sample_rate, channels, sample_width):
    import io

    buffer = io.BytesIO()
    wf = wave.open(buffer, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(sample_rate)
    wf.writeframes(samples)
    wf.close()
    buffer.seek(0)
    return buffer


def to_whisper_ndarray(frames, *, sample_rate, channels, sample_width):
    assert (sample_rate, channels, sample_width) == (16000, 1, 2), "16kHz 16bit mono"
    return (
        np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        / np.iinfo(np.int16).max
    )


async def record_audio(
    stop_event, channels=1, sample_rate=16000, format=pyaudio.paInt16, convert=to_wave
):
    frames_per_buffer = 1024
    p = pyaudio.PyAudio()
    stream = p.open(
        format=format,
        channels=channels,
        rate=sample_rate,
        frames_per_buffer=frames_per_buffer,
        input=True,
    )
    try:
        frames = []
        while not stop_event.is_set():
            data = stream.read(frames_per_buffer)
            frames.append(data)
            await asyncio.sleep(0.0)
        await stop_event.wait()

        return convert(
            b"".join(frames),
            sample_rate=sample_rate,
            channels=channels,
            sample_width=p.get_sample_size(format),
        )
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


# from pywhispercpp.constants import MODELS_DIR
MODEL_DIR = "/Users/pczapla/WorkDL/pywhispercpp/whisper.cpp/models"


class WhisperImpl(enum.Enum):
    cpp = "cpp"
    api = "api"
    realtime = "realtime"


class WhisperConfig(BaseSettings):
    whisper_model: str = Field(default="large-v3-turbo")
    whisper_impl: WhisperImpl = Field(default=WhisperImpl.cpp)
    models_dir: Path = Field(default=Path(MODEL_DIR))
    n_threads: int = Field(default=6)
    hotkey: str = Field(default="<F18>")
    model_config = SettingsConfigDict(env_prefix="sane_input_")
    language: str = Field(default="")


config = WhisperConfig()


class WhisperCppTranscriber:
    from pywhispercpp.model import Model

    def __init__(self):
        self.model = self.Model(
            config.whisper_model,
            models_dir=str(config.models_dir),
            n_threads=config.n_threads,
        )
        self.language = config.language

    async def __call__(self, audio_data: np.ndarray):
        segments = self.model.transcribe(audio_data, language=self.language)
        await asyncio.sleep(0)
        return " ".join([segment.text for segment in segments])


match (config.whisper_impl):
    case WhisperImpl.cpp:
        whisper_transcribe = WhisperCppTranscriber()
    case WhisperImpl.api:
        raise NotImplementedError("API not implemented")
    case WhisperImpl.realtime:
        raise NotImplementedError("Realtime not implemented")
    case _:
        raise ValueError(f"Invalid whisper implementation: {config.whisper_impl}")


async def dictate(key_released):
    print("recording")
    wave = await record_audio(key_released, convert=to_whisper_ndarray)
    print("transcribing")
    text = await whisper_transcribe(wave)
    print("pasting")
    await sane_output.paste_text(text)


async def main():
    global_hotkeys = sane_output.AsyncGlobalHotKeys({config.hotkey: dictate})
    await global_hotkeys.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
