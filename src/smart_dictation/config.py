import enum
from pathlib import Path

import pywhispercpp.constants
import pywhispercpp.model
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# from pywhispercpp.constants import MODELS_DIR
MODEL_DIR = pywhispercpp.constants.MODELS_DIR
print(MODEL_DIR)


class WhisperImpl(enum.Enum):
    cpp = "cpp"
    openai = "openai"
    realtime = "realtime"


class WhisperConfig(BaseSettings):
    whisper_model: str = Field(default="large-v3-turbo", alias="model")
    whisper_impl: WhisperImpl = Field(default=WhisperImpl.cpp, alias="implementation")
    whisper_models_dir: Path = Field(default=Path(MODEL_DIR), alias="models_dir")
    n_threads: int = Field(default=6, alias="threads")
    hotkey: str = Field(default="<ctrl>")
    language: str = Field(default="", alias="lang")
    input_device_index: int | None = Field(default=None)

    model_config = SettingsConfigDict(
        env_prefix="smart_dictation_", cli_parse_args=True
    )


cfg = WhisperConfig()
