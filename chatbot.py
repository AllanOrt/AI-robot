import ollama
import subprocess
import sys
import termios
import tty
import shutil
import os
import random
import time
import threading

# Hide cursor
print("\033[?25l", end="", flush=True)

def clear_screen():
    #Clear the terminal screen based on the OS.
    os.system('cls' if os.name == 'nt' else 'clear')

clear_screen()

# ASCII art displayed on launch
TEXT_ART = """
 ░▒▓███████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓███████▓▒░░▒▓███████▓▒░
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
░▒▓█▓▒░       ░▒▓█▓▒▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
 ░▒▓██████▓▒░ ░▒▓█▓▒▒▓█▓▒░░▒▓██████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
       ░▒▓█▓▒░ ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
       ░▒▓█▓▒░ ░▒▓█▓▓█▓▒░ ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
░▒▓███████▓▒░   ░▒▓██▓▒░  ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░
 Svarsenhet med Vanligtvis   Effektivt    Neuralt      Nätverk
"""

# Get terminal size and calculate position to center the ASCII art
cols, rows = shutil.get_terminal_size()
lines = TEXT_ART.strip().splitlines()
max_len = max(len(line) for line in lines)
start_x = (cols - max_len) // 2 + 1
start_y = (rows - len(lines)) // 2 + 1

# Control flag for glitch animation loop
glitching = True

def glitch_animation():
    # Continuously redraw the ASCII art with a glitch effect on each line except the last
    glitch_duration = 0.3  # seconds glitch lasts per line
    glitch_end_times = [0] * len(lines)  # track glitch end times for each line

    while glitching:
        for i in range(len(lines)):
            print(f"\033[{start_y + i};0H{' ' * (cols + 2)}", end="")
        now = time.time()

        for i, line in enumerate(lines):
            if i == len(lines) - 1:
                glitch = 0  # No glitch on last line
            else:
                if now < glitch_end_times[i]:
                    glitch = random.choice([-1, 1])
                else:
                    if random.random() < 0.0075:  # 0.5% chance to start glitch
                        glitch_end_times[i] = now + glitch_duration
                        glitch = random.choice([-1, 1])
                    else:
                        glitch = 0

            x_pos = start_x + glitch
            if i == 0:
                x_pos += 1  # compensate for first line offset

            print(f"\033[{start_y + i};{x_pos}H\033[32m{line}\033[0m")

        time.sleep(0.0625)

# Print the ASCII art initially without glitch
for i, line in enumerate(lines):
    x_pos = start_x + (1 if i == 0 else 0)
    print(f"\033[{start_y + i};{x_pos}H\033[32m{line}\033[0m")

# Start glitch animation in a background thread
glitch_thread = threading.Thread(target=glitch_animation, daemon=True)
glitch_thread.start()

# Model setup
model = 'slave:1b'
chat_history = []

def speak(text: str):
    #Speak a given text using espeak-ng with Swedish voice.
    if text.strip():
        subprocess.run(
            ["espeak-ng", "-v", "sv+m3", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

def hidden_input() -> str:
    #Read user input from terminal without echoing
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        chars = []
        while True:
            ch = sys.stdin.read(1)
            if ch in ('\n', '\r'):
                # Clear the current line before returning
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
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

try:
    while True:
        prompt = hidden_input()
        chat_history.append({"role": "user", "content": prompt})

        response = ""
        buffer = ""

        # Stream response from model
        for chunk in ollama.chat(model=model, messages=chat_history, stream=True):
            text = chunk['message']['content']
            response += text
            buffer += text

            # Speak complete sentences as they arrive
            while any(p in buffer for p in ['.', '!', '?']):
                for p in ['.', '!', '?']:
                    if p in buffer:
                        i = buffer.find(p)
                        sentence = buffer[:i+1].strip()
                        if sentence:
                            speak(sentence)
                        buffer = buffer[i+1:].lstrip()
                        break

        # Speak any remaining text after streaming ends
        if buffer.strip():
            speak(buffer.strip())

        chat_history.append({"role": "assistant", "content": response})

except KeyboardInterrupt:
    glitching = False
    glitch_thread.join()
    print("\033[?25h", end="", flush=True)  # Show cursor again
    os.system('cls' if os.name == 'nt' else 'clear')