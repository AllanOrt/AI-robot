import ollama
import subprocess
import sys
import termios
import tty
import shutil
import os
import time
import threading
import cv2
import RPi.GPIO as GPIO

# Constants
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
SLEEP_INTERVAL = 0.5

# Variables
dot_x = FRAME_WIDTH // 2  # Start dot horizontally in the middle
prev_dot_x_normalized = None
dot_x_lock = threading.Lock()  # Lock for thread-safe access to dot_x

# Load haar cascades
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize webcam
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

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

# Print commands
commands = [
    "#sv:    Ändra språket till Svenska",
    "#en:    Change the language to English",
    "#m:     Manlig röst",
    "#k:     Kvinnlig röst",
    "#göm:   Göm kommandomenyn",
    "#hjälp: Visa kommandomenyn",
    "#stäng: Stäng programmet"
]

clear_screen()
for i, line in enumerate(commands, start=1):
    print(f"\033[{i};1H\033[32m{line}\033[0m")

# Mouth ASCII arts
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
# Center the mouth in terminal
cols, rows = shutil.get_terminal_size()
lines = MOUTH_CLOSED.strip().splitlines()
max_len = max(len(line) for line in lines)
start_x = (cols - max_len) // 2 + 1
start_y = (rows - len(lines)) // 2 + 1

is_speaking = False
animation_thread = None
input_allowed = True
input_lock = threading.Lock()

def print_art(art):
    art_lines = art.strip().splitlines()
    for i, line in enumerate(art_lines):
        x_pos = start_x + (14 if i == 0 else 0)
        print(f"\033[{start_y + i};{x_pos}H\033[32m{line}\033[0m")

def mouth_animation():
    global is_speaking
    frame = False
    while is_speaking:
        current_frame = MOUTH_OPEN if frame else MOUTH_CLOSED
        frame = not frame
        print_art(current_frame)
        time.sleep(0.3)
    print_art(MOUTH_CLOSED)

print_art(MOUTH_CLOSED)

# Variables for chatbot
language_base = 'sv'
gender = 'm'
lang = f'{language_base}+{gender}3'
model = 'my_model:sv'
chat_history = []

def speak(text: str, lang: str):
    global is_speaking, animation_thread
    if text.strip():
        is_speaking = True
        if animation_thread is None or not animation_thread.is_alive():
            animation_thread = threading.Thread(target=mouth_animation, daemon=True)
            animation_thread.start()
        subprocess.run(
            ["espeak-ng", "-v", lang, text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        is_speaking = False
        if animation_thread:
            animation_thread.join()

def hidden_input() -> str:
    while not input_allowed:
        time.sleep(0.1)
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

def face_tracking():
    global dot_x, prev_dot_x_normalized

    ret, frame = camera.read()
    if not ret:
        return

    frame = cv2.flip(frame, 1)  # Mirror the frame horizontally
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected_faces = face_detector.detectMultiScale(gray_frame, 1.3, 5)

    if len(detected_faces) > 0:
        # Use the first detected face (or pick the largest one if needed)
        x, y, w, h = detected_faces[0]
        face_center_x = x + w // 2
        with dot_x_lock:
            dot_x = face_center_x

    # Normalize and print if changed
    with dot_x_lock:
        dot_x_normalized = round((dot_x / (FRAME_WIDTH - 1)) * 2 - 1, 2)

    if prev_dot_x_normalized != dot_x_normalized:
        print(f"\033[{rows};1H\033[33mX pos of face: {dot_x_normalized:.2f}\033[0m", end="", flush=True)
        prev_dot_x_normalized = dot_x_normalized

    time.sleep(SLEEP_INTERVAL)

def face_tracking_loop():
    try:
        while True:
            face_tracking()
    except Exception as e:
        print(f"Face tracking error: {e}")

# Start face tracking thread
face_thread = threading.Thread(target=face_tracking_loop, daemon=True)
face_thread.start()

try:
    while True:
        prompt = hidden_input()

        if prompt.strip() in ['#sv', '#en', '#m', '#f', '#k', '#hide', '#göm', '#help', '#hjälp', '#quit', '#stäng']:
            if prompt == '#sv':
                language_base = 'sv'
                lang = f'{language_base}+{gender}3'
                model = 'my_model:sv'
                commands = [
                    "#sv:    Ändra språket till Svenska",
                    "#en:    Change the language to English",
                    "#m:     Manlig röst",
                    "#k:     Kvinnlig röst",
                    "#göm:   Göm kommandomenyn",
                    "#hjälp: Visa kommandomenyn",
                    "#stäng: Stäng programmet"
                ]
                clear_screen()
                for i, line in enumerate(commands, start=1):
                    print(f"\033[{i};1H\033[32m{line}\033[0m")
                speak("Språket är nu sätt till svenska.", lang)

            elif prompt == '#en':
                language_base = 'en-us'
                lang = f'{language_base}+{gender}3'
                model = 'my_model:en'
                commands = [
                    "#sv:   Ändra språket till Svenska",
                    "#en:   Change the language to English",
                    "#m:    Male voice",
                    "#f:    Female voice",
                    "#hide  Hide the command menu",
                    "#help  Show the command menu",
                    "#quit: Close the program"
                ]
                clear_screen()
                for i, line in enumerate(commands, start=1):
                    print(f"\033[{i};1H\033[32m{line}\033[0m")
                speak("The language is now set to English.", lang)

            elif prompt == '#m':
                gender = 'm'
                lang = f'{language_base}+{gender}3'
                speak("Nu har jag en manlig röst." if language_base == 'sv' else "Now I have a male voice.", lang)

            elif prompt in ['#f', '#k']:
                gender = 'f'
                lang = f'{language_base}+{gender}3'
                speak("Nu har jag en kvinnlig röst." if language_base == 'sv' else "Now I have a female voice.", lang)

            elif prompt in ['#hide', '#göm']:
                commands = []
                clear_screen()
                print_art(MOUTH_CLOSED)

            elif prompt in ['#help', '#hjälp']:
                if lang == f'en+{gender}3':
                    commands = [
                        "#sv:   Ändra språket till Svenska",
                        "#en:   Change the language to English",
                        "#m:    Male voice",
                        "#f:    Female voice",
                        "#hide  Hide the command menu",
                        "#help  Show the command menu",
                        "#quit: Close the program"
                    ]
                elif lang == f'sv+{gender}3':
                    commands = [
                        "#sv:    Ändra språket till Svenska",
                        "#en:    Change the language to English",
                        "#m:     Manlig röst",
                        "#k:     Kvinnlig röst",
                        "#göm:   Göm kommandomenyn",
                        "#hjälp: Visa kommandomenyn",
                        "#stäng: Stäng programmet"
                    ]
                clear_screen()
                for i, line in enumerate(commands, start=1):
                    print(f"\033[{i};1H\033[32m{line}\033[0m")
                print_art(MOUTH_CLOSED)

            elif prompt in ['#quit', '#stäng']:
                is_speaking = False
                if animation_thread:
                    animation_thread.join()
                print("\033[?25h", end="", flush=True)

                for pin in GPIO_PINS.values():
                    GPIO.output(pin, GPIO.LOW)
                GPIO.cleanup()


                camera.release()
                clear_screen()

                break
            continue

        chat_history.append({"role": "user", "content": prompt})
        response = ""
        buffer = ""
        first_sentence_spoken = False

        input_allowed = False
        update_status("thinking")
        for chunk in ollama.chat(model=model, messages=chat_history, stream=True):
            text = chunk['message']['content']
            response += text
            buffer += text

            # Check if the first sentece has been spoken.
            if not first_sentence_spoken and any(p in buffer for p in ['.', '!', '?']):
                update_status("typing")
                first_sentence_spoken = True

            while any(p in buffer for p in ['.', '!', '?']):
                for p in ['.', '!', '?']:
                    if p in buffer:
                        i = buffer.find(p)
                        sentence = buffer[:i+1].strip()
                        if sentence:
                            speak(sentence, lang)
                        buffer = buffer[i+1:].lstrip()
                        break

        if buffer.strip():
            speak(buffer.strip(), lang)

        face_tracking()

        chat_history.append({"role": "assistant", "content": response})
        update_status("ready")
        input_allowed = True

except:
    is_speaking = False
    print("\033[?25h", end="", flush=True)

    for pin in GPIO_PINS.values():
        GPIO.output(pin, GPIO.LOW)
    GPIO.cleanup()

    camera.release()
    clear_screen()