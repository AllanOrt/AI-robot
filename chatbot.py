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
import RPi.GPIO as GPIO

# --- GPIO SETUP ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO_PINS = {
    "typing": 5,
    "thinking": 6,
    "ready": 13
}

for pin in GPIO_PINS.values():
    GPIO.setup(pin, GPIO.OUT)

def update_status(state: str):
    # Turn off all GPIO outputs
    for pin in GPIO_PINS.values():
        GPIO.output(pin, GPIO.LOW)

    # Set correct GPIO pin based on state
    if state == "Typing...":
        GPIO.output(GPIO_PINS["typing"], GPIO.HIGH)
    elif state == "Thinking...":
        GPIO.output(GPIO_PINS["thinking"], GPIO.HIGH)
    elif state == "You can type...":
        GPIO.output(GPIO_PINS["ready"], GPIO.HIGH)

    # Print status in top-right corner
    print(f"\033[1;{cols - len(state)}H\033[36m{state}\033[0m", end="", flush=True)

# Hide cursor
print("\033[?25l", end="", flush=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

clear_screen()

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

cols, rows = shutil.get_terminal_size()
lines = TEXT_ART.strip().splitlines()
max_len = max(len(line) for line in lines)
start_x = (cols - max_len) // 2 + 1
start_y = (rows - len(lines)) // 2 + 1

glitching = True

def glitch_animation():
    glitch_duration = 0.3
    glitch_end_times = [0] * len(lines)

    while glitching:
        for i in range(len(lines)):
            print(f"\033[{start_y + i};0H{' ' * (cols + 2)}", end="")
        now = time.time()

        for i, line in enumerate(lines):
            if i == len(lines) - 1:
                glitch = 0
            else:
                if now < glitch_end_times[i]:
                    glitch = random.choice([-1, 1])
                else:
                    if random.random() < 0.0075:
                        glitch_end_times[i] = now + glitch_duration
                        glitch = random.choice([-1, 1])
                    else:
                        glitch = 0

            x_pos = start_x + glitch
            if i == 0:
                x_pos += 1

            print(f"\033[{start_y + i};{x_pos}H\033[32m{line}\033[0m")

        time.sleep(0.0625)

for i, line in enumerate(lines):
    x_pos = start_x + (1 if i == 0 else 0)
    print(f"\033[{start_y + i};{x_pos}H\033[32m{line}\033[0m")

glitch_thread = threading.Thread(target=glitch_animation, daemon=True)
glitch_thread.start()

model = 'slave:1b'
chat_history = []

def speak(text: str):
    if text.strip():
        subprocess.run(
            ["espeak-ng", "-v", "sv+m3", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

def hidden_input() -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        chars = []
        while True:
            ch = sys.stdin.read(1)
            if ch in ('\n', '\r'):
                sys.stdout.write('\r\x1b[2K')
                sys.stdout.flush()
                break
            elif ch == '\x03':
                raise KeyboardInterrupt
            elif ch == '\x7f' and chars:
                chars.pop()
            else:
                chars.append(ch)
        return ''.join(chars)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

try:
    while True:
        update_status("You can type...")
        prompt = hidden_input()
        chat_history.append({"role": "user", "content": prompt})

        response = ""
        buffer = ""
        first_sentence_spoken = False

        update_status("Thinking...")
        for chunk in ollama.chat(model=model, messages=chat_history, stream=True):
            text = chunk['message']['content']
            response += text
            buffer += text

            if not first_sentence_spoken and any(p in buffer for p in ['.', '!', '?']):
                update_status("Typing...")
                first_sentence_spoken = True

            while any(p in buffer for p in ['.', '!', '?']):
                for p in ['.', '!', '?']:
                    if p in buffer:
                        i = buffer.find(p)
                        sentence = buffer[:i+1].strip()
                        if sentence:
                            speak(sentence)
                        buffer = buffer[i+1:].lstrip()
                        break

        if buffer.strip():
            speak(buffer.strip())

        chat_history.append({"role": "assistant", "content": response})
        update_status("You can type...")

except KeyboardInterrupt:
    glitching = False
    glitch_thread.join()
    print("\033[?25h", end="", flush=True)
    GPIO.cleanup()
    os.system('cls' if os.name == 'nt' else 'clear')
