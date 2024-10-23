import asyncio
import io
import wave

import pyaudio

from smart_dictation import hotkeys

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


def get_default_device() -> tuple[int, str]:
    """Retrieve the default input sound device index."""
    p = pyaudio.PyAudio()
    try:
        val = p.get_default_input_device_info()
        return int(val["index"]), str(val["name"])
    finally:
        p.terminate()
    return None, "default"


async def record_audio(
    stop_event,
    channels=1,
    sample_rate=SAMPLE_RATE,
    format=pyaudio.paInt16,
    convert=to_wave,
    device=None,
):
    frames_per_buffer = 1024
    p = pyaudio.PyAudio()
    stream = p.open(
        format=format,
        channels=channels,
        rate=sample_rate,
        frames_per_buffer=frames_per_buffer,
        input=True,
        input_device_index=device,
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
            raise hotkeys.StopTask("Too short audio")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


def get_sound_devices() -> list:
    """Retrieve a list of input sound devices."""
    p = pyaudio.PyAudio()
    devices = []
    info = p.get_host_api_info_by_index(0)
    numdevices = int(info.get("deviceCount", 0))
    for i in range(numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if int(device_info.get("maxInputChannels", 0)) > 0:
            devices.append((device_info.get("index"), device_info.get("name")))
    p.terminate()
    return devices


def get_device_info(device_index):
    if device_index is None:
        return {"name": "default"}
    p = pyaudio.PyAudio()
    return p.get_device_info_by_host_api_device_index(0, device_index)
