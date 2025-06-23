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

# GPIO setup
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

    # Turn on the pin for the given state
    pin = GPIO_PINS.get(state)
    if pin is not None:
        GPIO.output(pin, GPIO.HIGH)

# Hide cursor
print("\033[?25l", end="", flush=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

clear_screen()

MOUTH_CLOSED = """
              ▄▄▄▄▄▄          ▄▄▄▄▄▄              
           ▄▀▀      ▀▀▀▀▀▀▀▀▀▀      ▀▀▄           
         ▄▀                            ▀▄         
     ▄▄▀▀                                ▀▀▄▄     
 ▄▄██▄▄▄▄▄▄▄▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄▄▄▄▄▄▄▄██▄▄ 
▀▀▀▄▄                                        ▄▄▀▀▀
     ▀▀▄                                  ▄▀▀     
        ▀▀▀▄▄                        ▄▄▀▀▀        
             ▀▀▀▀▀▄▄▄        ▄▄▄▀▀▀▀▀             
                     ▀▀▀▀▀▀▀▀                     
"""

MOUTH_OPEN = """
              ▄▄▄▄▄▄          ▄▄▄▄▄▄              
           ▄▀▀      ▀▀▀▀▀▀▀▀▀▀      ▀▀▄           
         ▄▀                            ▀▄         
     ▄▄▀▀         ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄        ▀▀▄▄     
 ▄▄██▄▄▄▄▄▄▀▀▀▀▀▀▀               ▀▀▀▀▀▀▄▄▄▄▄▄██▄▄ 
▀▀▀▄▄    ▀▀▀▀▀▄▄▄▄▄            ▄▄▄▄▄▀▀▀▀▀    ▄▄▀▀▀
     ▀▀▄           ▀▀▀▀▀▀▀▀▀▀▀▀           ▄▀▀     
        ▀▀▀▄▄                        ▄▄▀▀▀        
             ▀▀▀▀▀▄▄▄        ▄▄▄▀▀▀▀▀             
                     ▀▀▀▀▀▀▀▀                     
"""

cols, rows = shutil.get_terminal_size()
lines = MOUTH_CLOSED.strip().splitlines()
max_len = max(len(line) for line in lines)
start_x = (cols - max_len) // 2 + 1
start_y = (rows - len(lines)) // 2 + 1

glitching = True
is_speaking = False

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
                x_pos += 14    # To compensate for the removal of leading white spaces

            print(f"\033[{start_y + i};{x_pos}H\033[32m{line}\033[0m")

        time.sleep(0.0625)

def speaking_animation():
    global is_speaking
    frame = False
    while glitching:
        if is_speaking:
            current_frame = MOUTH_OPEN if frame else MOUTH_CLOSED
            frame = not frame
            frame_lines = current_frame.strip().splitlines()
            for i, line in enumerate(frame_lines):
                x_pos = start_x + (1 if i == 0 else 0)
                print(f"\033[{start_y + i};{x_pos}H\033[32m{line}\033[0m")
            time.sleep(0.3)
        else:
            time.sleep(0.05)

for i, line in enumerate(lines):
    x_pos = start_x + (1 if i == 0 else 0)
    print(f"\033[{start_y + i};{x_pos}H\033[32m{line}\033[0m")

glitch_thread = threading.Thread(target=glitch_animation, daemon=True)
glitch_thread.start()

speaking_thread = threading.Thread(target=speaking_animation, daemon=True)
speaking_thread.start()

model = 'slave:1b'
chat_history = []

def speak(text: str):
    global is_speaking

    def run_speech():
        nonlocal text
        if text.strip():
            is_speaking = True
            subprocess.run(
                ["espeak-ng", "-v", "sv+m3", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            is_speaking = False

    t = threading.Thread(target=run_speech)
    t.start()
    t.join()

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
        update_status("ready")
        prompt = hidden_input()
        chat_history.append({"role": "user", "content": prompt})

        response = ""
        buffer = ""
        first_sentence_spoken = False

        update_status("thinking")
        for chunk in ollama.chat(model=model, messages=chat_history, stream=True):
            text = chunk['message']['content']
            response += text
            buffer += text

            if not first_sentence_spoken and any(p in buffer for p in ['.', '!', '?']):
                update_status("typing")
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
        update_status("ready")

except KeyboardInterrupt:
    glitching = False
    glitch_thread.join()
    speaking_thread.join()
    print("\033[?25h", end="", flush=True)
    
    # Turn off all lamps explicitly before cleanup
    for pin in GPIO_PINS.values():
        GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()

    os.system('cls' if os.name == 'nt' else 'clear')