# AI robot
An AI robot running on a Raspberry Pi 4B with 8gb ram. It uses a quantized Gemma3 one billion perameter, with ollama. It has blinking lights and other cool stuff :)

# How to install
1. Install ollama:
 ```curl -fsSL https://ollama.com/install.sh | sh ```
 
2. Install the model: ```ollama pull gemma3:1b```

3. Edit the prompt in the Modelfile

4. Turn it into a model (replace my_model in chatbot.py with the name you gave it): ```ollama create my_model -f Modelfile```

5. Install eSpeak (I have it set to Swedish, change it to English by replacing "sv+m3" with "en+m3" in chatbot.py): ```sudo apt install espeak-ng```

6. Install the requierd packages: ```pip install -r requirements.txt```

7. Run chatbot.py! ```python3 chatbot.py```
