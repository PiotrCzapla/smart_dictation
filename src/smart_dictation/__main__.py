import asyncio
import enum
import typer
import structlog
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import pywhispercpp.constants
from smart_dictation.app import start_listening, list_sound_devices
from smart_dictation.local_whisper import WhisperCppTranscriber
from smart_dictation.config import cfg

app = typer.Typer()


@app.command()
def list_devices():
    list_sound_devices()


@app.command()
def listen(device: int | None = None):
    cfg.input_device_index = device
    asyncio.run(start_listening())


if __name__ == "__main__":
    app()
