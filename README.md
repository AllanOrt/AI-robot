# AI robot
An AI robot running on a Raspberry Pi 4B with 8gb ram. It uses a quantized Gemma3 one billion perameter, with ollama. It has blinking lights and other cool stuff :)<br><br>
<img src="logo.png" alt="Icon" width="600px">

# How to install
1. Wire your Raspberry Pi like this:<br>
<img src="scematic.png" alt="Icon" width="600px">

3. Install ollama:
 ```curl -fsSL https://ollama.com/install.sh | sh ```
 
4. Install the model: ```ollama pull gemma3:1b```

5. Edit the prompt in the Modelfile

6. Turn it into a model (replace my_model in chatbot.py with the name you gave it): ```ollama create my_model -f Modelfile```

8. This step is optional, but sinze I live in Sweden I made a swedish model too, so two in total. The swedish was named ```my_model:sv ``` and the english one ```my_model:en```

7. Install eSpeak: ```sudo apt install espeak-ng```

8. Install the requierd packages: ```pip install -r requirements.txt```

9. Run chatbot.py! ```python3 chatbot.py```
