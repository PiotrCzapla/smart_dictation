import pytest
import wave
import asyncio
import io
from unittest.mock import MagicMock, patch
from smart_dictation.audio import (
    to_wave,
    infer_time,
    record_audio,
    get_sound_devices,
)


def test_to_wave():
    samples = b"\x00\x01\x02\x03"
    sample_rate = 16000
    channels = 1
    sample_width = 2
    wave_buffer = to_wave(
        samples, sample_rate=sample_rate, channels=channels, sample_width=sample_width
    )
    assert isinstance(wave_buffer, io.BytesIO)
    wave_buffer.seek(0)
    with wave.open(wave_buffer, "rb") as wf:
        assert wf.getnchannels() == channels
        assert wf.getsampwidth() == sample_width
        assert wf.getframerate() == sample_rate


def test_infer_time():
    samples = b"\x00\x01\x02\x03" * 2000  # 8000 bytes
    expected_time = 0.25  # 8000 / 16000 / 2
    assert infer_time(samples) == expected_time


@pytest.mark.asyncio
async def test_record_audio():
    stop_event = asyncio.Event()

    with patch("pyaudio.PyAudio") as mock_pyaudio:
        mock_stream = MagicMock()
        mock_pyaudio.return_value.open.return_value = mock_stream
        mock_stream.read.return_value = b"\x00\x01\x02\x03" * 8000
        asyncio.get_event_loop().call_later(0.1, stop_event.set)
        convert = lambda x, **kw: "converted"
        result = await record_audio(stop_event, convert=convert)
        assert result == "converted"


def test_get_sound_devices():
    with patch("pyaudio.PyAudio") as mock_pyaudio:
        mock_pyaudio.return_value.get_host_api_info_by_index.return_value = {
            "deviceCount": 1
        }
        mock_pyaudio.return_value.get_device_info_by_host_api_device_index.return_value = {
            "maxInputChannels": 1,
            "name": "Mock Device",
        }
        devices = get_sound_devices()
        assert len(devices) == 1
        assert devices[0][1] == "Mock Device"
