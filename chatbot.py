import ollama
import subprocess

model_name = 'slave:1b'
messages = []

def speak(text):
    if text.strip():
        subprocess.run(["espeak-ng", "-v", "sv+m3", text],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

while True:
    user_input = input("Du: ")
    if not user_input:
        break

    messages.append({"role": "user", "content": user_input})

    print("Bot:", end=' ', flush=True)
    response = ""
    sentence_buffer = ""

    for chunk in ollama.chat(model=model_name, messages=messages, stream=True):
        content = chunk['message']['content']
        print(content, end='', flush=True)
        response += content
        sentence_buffer += content

        # Check for sentence-ending punctuation
        while any(p in sentence_buffer for p in ['.', '!', '?']):
            for p in ['.', '!', '?']:
                if p in sentence_buffer:
                    idx = sentence_buffer.find(p)
                    sentence = sentence_buffer[:idx + 1].strip()
                    if sentence:
                        speak(sentence)
                    sentence_buffer = sentence_buffer[idx + 1:].lstrip()
                    break

    # Speak any remaining sentence part
    if sentence_buffer.strip():
        speak(sentence_buffer.strip())

    print()
    messages.append({"role": "assistant", "content": response})
