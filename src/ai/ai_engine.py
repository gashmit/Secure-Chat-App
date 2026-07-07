import pyttsx3
import speech_recognition as sr
import whisper
import threading
import os
import tempfile
from deep_translator import GoogleTranslator

class AudioTranslationEngine:
    # This is the exact dictionary your UI is looking for!
    SUPPORTED_LANGUAGES = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Japanese": "ja",
        "Hindi": "hi",
        "Arabic": "ar",
        "Russian": "ru"
    }

    def __init__(self, target_code='es'):
        print("System: Loading Whisper Neural Network... (This takes a few seconds)")
        # UPDATE 1: Change "base" to "small" (Requires a ~460MB download on first run)
        self.stt_model = whisper.load_model("small") 
        
        self.tts = pyttsx3.init()
        self.tts.setProperty('rate', 175) 
        
        self.current_target = target_code
        self.translator = GoogleTranslator(source='auto', target=self.current_target)
        
        self.recognizer = sr.Recognizer()

    def set_target_language(self, language_name: str):
        if language_name in self.SUPPORTED_LANGUAGES:
            self.current_target = self.SUPPORTED_LANGUAGES[language_name]
            self.translator = GoogleTranslator(source='auto', target=self.current_target)
            print(f"System: Translation engine switched to {language_name} ({self.current_target})")
        else:
            print(f"System Error: {language_name} is not in the supported languages list.")

    def listen_and_transcribe(self) -> str:
        with sr.Microphone() as source:
            print("System: Adjusting for ambient noise...")
            # UPDATE 2: Change duration from 0.5 to 1.0 seconds for better noise cancellation
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            print("System: Listening (Speak now!)...")
            
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("System: Processing audio locally with Whisper...")
                
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                    temp_wav.write(audio.get_wav_data())
                    temp_filename = temp_wav.name
                    
                result = self.stt_model.transcribe(temp_filename)
                os.remove(temp_filename)
                
                return result["text"].strip()
                
            except sr.WaitTimeoutError:
                return ""
            except Exception as e:
                return f"[Audio Error: {e}]"

    def translate_text(self, text: str) -> str:
        if not text or text.startswith("["):
            return text
        try:
            return self.translator.translate(text)
        except Exception as e:
            return f"[Translation Error: {e}]"

    def speak(self, text: str):
        def _speak_thread():
            self.tts.say(text)
            self.tts.runAndWait()
            
        threading.Thread(target=_speak_thread, daemon=True).start()