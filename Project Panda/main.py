import speech_recognition as sr
import pyttsx3
import webbrowser
import pyjokes
import random
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes.client import CreateObject
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import tkinter as tk
from tkinter import Label, Canvas
from PIL import Image, ImageTk
from threading import Thread

# Initialize recognizer and engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

# GUI Setup
class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Panda Assistant")
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes('-topmost', True)  # Always on top
        self.root.configure(bg='black')  # Transparent background

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Set window size and position (bottom center)
        window_width = 60
        window_height = 60
        x_position = (screen_width // 2) - (window_width // 2)
        y_position = screen_height - 100  # Above the taskbar
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # Load images
        self.mic_image = Image.open("microphone.png").resize((50, 50), Image.LANCZOS)
        self.bubble_image = Image.open("bubble.png").resize((100, 50), Image.LANCZOS)
        self.mic_icon = ImageTk.PhotoImage(self.mic_image)
        self.bubble_icon = ImageTk.PhotoImage(self.bubble_image)

        # Create canvas for images
        self.canvas = Canvas(root, bg="black", highlightthickness=0, width=window_width, height=window_height)
        self.canvas.pack()

        # Start with microphone icon
        self.current_image = self.canvas.create_image(30, 30, image=self.mic_icon)

    def update_icon(self, listening):
        """Switch between microphone and bubble icons."""
        self.canvas.delete(self.current_image)
        if listening:
            self.current_image = self.canvas.create_image(50, 25, image=self.bubble_icon)
        else:
            self.current_image = self.canvas.create_image(30, 30, image=self.mic_icon)

# Initialize GUI
root = tk.Tk()
gui = AssistantGUI(root)

def speak(text):
    engine.say(text)
    engine.runAndWait()

def set_volume(change):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    
    current_volume = volume.GetMasterVolumeLevelScalar()
    new_volume = max(0.0, min(1.0, current_volume + change))
    volume.SetMasterVolumeLevelScalar(new_volume, None)

    speak(f"Volume {'increased' if change > 0 else 'decreased'}.")

def set_brightness(change):
    current_brightness = sbc.get_brightness()
    new_brightness = max(10, min(100, current_brightness[0] + change))
    sbc.set_brightness(new_brightness)

    speak(f"Brightness {'increased' if change > 0 else 'decreased'}.")

def listen_for_wake_word():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        gui.update_icon(False)  # Show microphone icon
        while True:
            try:
                audio = recognizer.listen(source, timeout=None)
                wake_word = recognizer.recognize_google(audio).lower()
                if "panda" in wake_word:
                    gui.update_icon(True)  # Show bubble icon
                    speak("Yes?")
                    return True
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print("Error:", e)

def listen_for_command():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        gui.update_icon(True)  # Show bubble icon
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
            command = recognizer.recognize_google(audio).lower()
            print("You said:", command)

            if "stop" in command:
                speak("Stopping Panda.")
                exit()
            
            elif "increase volume" in command:
                set_volume(0.1)
            
            elif "decrease volume" in command:
                set_volume(-0.1)

            elif "increase brightness" in command:
                set_brightness(10)

            elif "decrease brightness" in command:
                set_brightness(-10)
                
            elif "open" in command:
                if "google" in command:
                    webbrowser.open("https://www.google.com")
                    speak("Opening Google.")
                elif "youtube" in command:
                    webbrowser.open("https://www.youtube.com")
                    speak("Opening YouTube.")
                elif "facebook" in command:
                    webbrowser.open("https://www.facebook.com")
                    speak("Opening Facebook.")
                elif "instagram" in command:
                    webbrowser.open("https://www.instagram.com")
                    speak("Opening Instagram.")
                else:
                    speak("Sorry, I don't know that website.")
            
            elif "search" in command:
                search_query = command.replace("search", "").strip()
                webbrowser.open(f"https://www.google.com/search?q={search_query}")
                speak(f"Searching for {search_query} on Google.")
            
            elif "tell me a joke" in command:
                while True:
                    joke = pyjokes.get_joke()
                    speak(f"Here's a joke: {joke}. Would you like another one?")
                    print("Listening for response...")

                    try:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                        response = recognizer.recognize_google(audio).lower()
                        print("User response:", response)

                        if "yes" in response:
                            speak("Got it!")
                            continue
                        elif "no" in response:
                            speak("Alright, no more jokes for now.")
                            break
                        else:
                            speak("I didn't catch that. Please say yes or no.")
                    except sr.WaitTimeoutError:
                        speak("I didn't hear a response. Stopping jokes.")
                        break
                    except sr.UnknownValueError:
                        speak("I couldn't understand you. Please say yes or no.")
            
            elif "give your introduction" in command:
                introductions = [
                    "Hello! I am Panda, your personal voice assistant. How can I help you today?",
                    "Hey there! I am Panda, a smart assistant ready to assist you. What do you need?",
                    "Hi! I'm Panda, an AI-powered voice assistant. Let's make your life easier!"
                ]
                speak(random.choice(introductions))
            
            else:
                speak("Sorry, I didn't understand the command.")
            
        except sr.WaitTimeoutError:
            print("No command detected.")
        except sr.UnknownValueError:
            print("Could not understand.")
        except Exception as e:
            print("Error:", e)

def run_assistant():
    speak("Initializing Panda....")
    while True:
        if listen_for_wake_word():
            listen_for_command()

# Run the assistant in a separate thread
assistant_thread = Thread(target=run_assistant)
assistant_thread.daemon = True
assistant_thread.start()

# Start the GUI main loop
root.mainloop()