import enum
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import pywhispercpp.model
import pywhispercpp.constants

# from pywhispercpp.constants import MODELS_DIR
MODEL_DIR = pywhispercpp.constants.MODELS_DIR
print(MODEL_DIR)


class WhisperImpl(enum.Enum):
    cpp = "cpp"
    api = "api"
    realtime = "realtime"


class WhisperConfig(BaseSettings):
    whisper_model: str = Field(default="large-v3-turbo")
    whisper_impl: WhisperImpl = Field(default=WhisperImpl.cpp)
    whisper_models_dir: Path = Field(default=Path(MODEL_DIR))
    n_threads: int = Field(default=6)
    hotkey: str = Field(default="<ctrl>+<alt>+<shift>+<cmd>")
    model_config = SettingsConfigDict(env_prefix="smart_dictation_")
    language: str = Field(default="")
    input_device_index: int | None = Field(default=None)

cfg = WhisperConfig()
