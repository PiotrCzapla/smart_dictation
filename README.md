# Smart Dictation
A fast, accurate, and open-source dictation app with an auditable codebase. 

By building on top of whisper.cpp, we can achieve very high accuracy with relatively short delay for large-v3-turbo (2 seconds per 30 seconds of audio on M1 Pro).

**Disclaimer:**
This is a first prototype. It works for me on macOS, but it hasn't been extensively tested. However, feel free to try it.

## Installation
### macOS
```sh
brew install portaudio # for pyaudio 
brew install uv # alternative to pip for dependency management
git clone https://github.com/PiotrCzapla/smart_dictation.git
cd smart_dictation

uv sync

.venv/bin/smart_dictation --hotkey "<ctrl>" --model "base" # base is fast, but large-v3-turbo is more accurate
```

The app listens to your keyboard, and when the selected keys are pressed, it records the audio. Upon release, it transcribes and pastes the text into the currently active window. Therefore, the terminal running it needs accessibility permission and permission to record audio.

#### CoreML

Currently, the CoreML models are not being distributed via whisper.cpp. Once there is a distribution channel, I will update the app. In the meantime, if you want to speed up of CoreML, follow the instructions in whisper.cpp to build the models: https://github.com/ggerganov/whisper.cpp#core-ml-support

### Windows
I haven't tested the repository extensively, but it works with a workaround. The pywhispercpp build process requires MS Visual Studio, and uv needs a short temporary directory; otherwise, the Visual Studio compiler will fail. See https://github.com/abdeladim-s/pywhispercpp/issues/78 for more details.
