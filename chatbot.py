# Imports
import ollama
import subprocess
import sys
import termios
import tty
import shutil
import os

print("\033[?25l", end="", flush=True) # Hide cursor

# Clear screen depending on OS
if os.name == 'nt':
    os.system('cls')
else:
    os.system('clear')

# ASCII art to display on launch
text_art = """
 ░▒▓███████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓███████▓▒░░▒▓███████▓▒░
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
░▒▓█▓▒░       ░▒▓█▓▒▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
 ░▒▓██████▓▒░ ░▒▓█▓▒▒▓█▓▒░░▒▓██████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
       ░▒▓█▓▒░ ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
       ░▒▓█▓▒░ ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
░▒▓███████▓▒░   ░▒▓██▓▒░  ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
"""

# Get terminal size to center the text art
cols, rows = shutil.get_terminal_size()
lines = text_art.strip().splitlines()
max_len = max(len(line) for line in lines)
start_x = (cols - max_len) // 2 + 1
start_y = (rows - len(lines)) // 2 + 1

# Print the ASCII art centered
for i, line in enumerate(lines):
    x_pos = start_x + 1 if i == 0 else start_x # Offset the first line to the right, because it collapses white space    
    print(f"\033[{start_y + i};{x_pos}H\033[32m{line}\033[0m")# Print it green

# Setup model and conversation history
model = 'my_model'
chat_history = []

# Function to speak a line using espeak-ng
def speak(text):
    if text.strip():
        subprocess.run(["espeak-ng", "-v", "sv+m3", text],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Reads input from user
def hidden_input():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        chars = []
        while True:
            ch = sys.stdin.read(1)
            if ch in ('\n', '\r'):
                sys.stdout.write('\r\x1b[2K')
                sys.stdout.flush()
                break
            elif ch == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            elif ch == '\x7f' and chars:  # Backspace
                chars.pop()
            else:
                chars.append(ch)
        return ''.join(chars)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# Main input/output loop
while True:
    try:
        prompt = hidden_input()
    except KeyboardInterrupt:
        print("\033[?25h", end="", flush=True) # Show curser
        break

    if not prompt:
        break

    # Add user prompt to chat history
    chat_history.append({"role": "user", "content": prompt})

    response = ""
    buffer = ""

    # Stream response from model
    for chunk in ollama.chat(model=model, messages=chat_history, stream=True):
        text = chunk['message']['content']
        response += text
        buffer += text

        # Speak completed sentences as they arrive
        while any(p in buffer for p in ['.', '!', '?']):
            for p in ['.', '!', '?']:
                if p in buffer:
                    i = buffer.find(p)
                    sentence = buffer[:i+1].strip()
                    if sentence:
                        speak(sentence)
                    buffer = buffer[i+1:].lstrip()
                    break

    # Speak any remaining text
    if buffer.strip():
        speak(buffer.strip())

    # Add response to chat history
    chat_history.append({"role": "assistant", "content": response})