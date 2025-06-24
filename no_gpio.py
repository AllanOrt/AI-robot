import ollama
import subprocess
import sys
import termios
import tty
import shutil
import os
import time
import threading

# Hide cursor
print("\033[?25l", end="", flush=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Print commands
commands = [
    "#sv:   Ändra språket till Svenska",
    "#en:   Change the language to English",
    "#stäng: Stäng programmet"
]

clear_screen()  # Clear first so commands show cleanly
for i, line in enumerate(commands, start=1):
    print(f"\033[{i};1H\033[32m{line}\033[0m")

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

is_speaking = False
animation_thread = None

def print_art(art):
    art_lines = art.strip().splitlines()
    for i, line in enumerate(art_lines):
        x_pos = start_x + (14 if i == 0 else 0)    # shift first line 14 chars right to compensate for removal of leading white space
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

# Print initial mouth closed art
print_art(MOUTH_CLOSED)

model = 'my_model:sv'
lang = 'sv+m3'  # Default language is Swedish
chat_history = []


def speak(text: str, lang: str):
    global is_speaking, animation_thread

    if text.strip():
        is_speaking = True

        # Start animation thread if not running
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
        prompt = hidden_input()

        if prompt.strip() in ['#sv', '#en', '#quit', '#stäng']:
            if prompt == '#sv':

                lang = 'sv+m3'    # Change the language to Swedish
                model = 'my_model:sv'
                # Print commands
                commands = [
                    "#sv:   Ändra språket till Svenska",
                    "#en:   Change the language to English",
                    "#stäng: Stäng programmet"
                ]
                clear_screen()  # Clear first so commands show cleanly
                for i, line in enumerate(commands, start=1):
                    print(f"\033[{i};1H\033[32m{line}\033[0m")
                speak("Språket är nu sätt till svenska.", lang)
            elif prompt == '#en':
                lang = 'en-us+m3'    # Change the language to English
                model = 'my_model:en'# Print commands
                commands = [
                    "#sv:   Ändra språket till Svenska",
                    "#en:   Change the language to English",
                    "#quit: Close the program"
                ]
                clear_screen()  # Clear first so commands show cleanly
                for i, line in enumerate(commands, start=1):
                    print(f"\033[{i};1H\033[32m{line}\033[0m")
                speak("The language is now set to English.", lang)
            elif prompt in ['#quit', '#stäng']:
                is_speaking = False
                if animation_thread:
                    animation_thread.join()
                print("\033[?25h", end="", flush=True)

                clear_screen()
                break
            continue

        chat_history.append({"role": "user", "content": prompt})

        response = ""
        buffer = ""
        first_sentence_spoken = False

        for chunk in ollama.chat(model=model, messages=chat_history, stream=True):
            text = chunk['message']['content']
            response += text
            buffer += text

            if not first_sentence_spoken and any(p in buffer for p in ['.', '!', '?']):
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

        chat_history.append({"role": "assistant", "content": response})

except KeyboardInterrupt:
    is_speaking = False
    if animation_thread:
        animation_thread.join()
    print("\033[?25h", end="", flush=True)

    clear_screen()
