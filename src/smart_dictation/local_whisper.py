import asyncio
import numpy as np
import pywhispercpp.model
import structlog
from smart_dictation.config import cfg
from functools import cached_property


def to_whisper_ndarray(frames, *, sample_rate, channels, sample_width):
    assert (sample_rate, channels, sample_width) == (16000, 1, 2), "16kHz 16bit mono"
    return (
        np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        / np.iinfo(np.int16).max
    )


class WhisperCppTranscriber:
    def __init__(self):
        pywhispercpp.model.logging = structlog.get_logger()
        self.language = cfg.language

    @cached_property
    def model(self):
        return pywhispercpp.model.Model(
            cfg.whisper_model,
            models_dir=str(cfg.whisper_models_dir),
            n_threads=cfg.n_threads,
        )

    def preload(self):
        self.model

    async def __call__(self, audio_data: np.ndarray):
        segments = self.model.transcribe(audio_data, language=self.language)
        await asyncio.sleep(0)
        return " ".join([segment.text for segment in segments])
