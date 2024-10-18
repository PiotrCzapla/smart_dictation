# Smart Dictation
Using whisper.cpp with coreml support and turbo version of large v3 whisper mmodel we get around a 2 sec delay for 30 sec dictation.



## Prerequisites
We use pyaudio a binding to portAudio that needs to be installed with `brew install portaudio`. 

Dictation speed, by accident I've recorded: 35 min of audio which took 163 sec to trascirbe 