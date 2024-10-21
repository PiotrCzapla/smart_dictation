import asyncio
import enum
import io
import wave
from pathlib import Path

import pyaudio
import structlog
import typer
from pydantic import Field

from smart_dictation import sane_output

SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2


def to_wave(samples, *, sample_rate, channels, sample_width):
    buffer = io.BytesIO()
    wf = wave.open(buffer, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(sample_width)
    wf.setframerate(sample_rate)
    wf.writeframes(samples)
    wf.close()
    buffer.seek(0)
    return buffer


def infer_time(samples, *, sample_rate=SAMPLE_RATE, sample_width=SAMPLE_WIDTH):
    return len(samples) / sample_rate / sample_width


async def record_audio(
    stop_event,
    channels=1,
    sample_rate=SAMPLE_RATE,
    format=pyaudio.paInt16,
    convert=to_wave,
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
        samples = b"".join(frames)
        if infer_time(samples) > 1.0:
            return convert(
                b"".join(frames),
                sample_rate=sample_rate,
                channels=channels,
                sample_width=p.get_sample_size(format),
            )
        else:
            raise sane_output.StopTask("Too short audio")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


def get_sound_devices() -> list:
    """Retrieve a list of input sound devices."""
    p = pyaudio.PyAudio()
    devices = []
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get("deviceCount")
    for i in range(numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get("maxInputChannels") > 0:
            devices.append((i, device_info.get("name")))
    p.terminate()
    return devices
