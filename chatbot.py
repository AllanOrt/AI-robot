import ollama
import subprocess

model_name = 'slave:1b'
messages = []

def speak(word):
    # Speak a word using espeak-ng with Swedish voice
    subprocess.run(["espeak-ng", "-v", "sv+m3", word],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

while True:
    user_input = input("Du: ")
    if not user_input:
        break

    messages.append({"role": "user", "content": user_input})

    print("Bot:", end=' ', flush=True)
    response = ""
    buffer = ""

    for chunk in ollama.chat(model=model_name, messages=messages, stream=True):
        content = chunk['message']['content']
        print(content, end='', flush=True)
        response += content
        buffer += content

        # Speak word when space or punctuation is detected
        while any(sep in buffer for sep in [' ', '.', '!', '?']):
            for sep in [' ', '.', '!', '?']:
                if sep in buffer:
                    idx = buffer.find(sep)
                    word = buffer[:idx + 1].strip()
                    if word:
                        speak(word)
                    buffer = buffer[idx + 1:]
                    break

    # Speak any remaining word
    if buffer.strip():
        speak(buffer.strip())

    print()
    messages.append({"role": "assistant", "content": response})
