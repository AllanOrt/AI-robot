from vosk import Model, KaldiRecognizer
import pyaudio
import json

model = Model("vosk-model-small-sv-rhasspy-0.15")
recognizer = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

print("Listening...")

while True:
    data = stream.read(4000, exception_on_overflow=False)
    if recognizer.AcceptWaveform(data):
        print(json.loads(recognizer.Result())["text"])
    # else: partial results ignored for brevity
