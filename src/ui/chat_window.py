import customtkinter as ctk
import socket
import threading
from src.security.session_manager import SecureSession
from src.ai.ai_engine import AudioTranslationEngine

# Set the overall theme and color
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SecureChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Secure E2EE Chat - Multimodal AI")
        self.geometry("650x750")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Network & Security State
        self.conn = None 
        self.session = SecureSession()
        self.is_host = False

        # Initialize AI Engine (This loads the "small" Whisper model)
        self.ai_engine = AudioTranslationEngine()
        
        # Default state for the new toggle
        self.auto_translate = False

        self.setup_lobby_screen()
        self.setup_chat_screen()
        
        # Start in the lobby
        self.show_lobby()

    # ================= UI SETUP =================
    
    def setup_lobby_screen(self):
        self.lobby_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        title = ctk.CTkLabel(self.lobby_frame, text="Secure E2EE Chat", font=("Arial", 28, "bold"))
        title.pack(pady=(100, 50))

        # Host Section
        host_btn = ctk.CTkButton(self.lobby_frame, text="Host a Secure Session", font=("Arial", 16), height=50, command=self.start_server_thread)
        host_btn.pack(pady=10, fill="x", padx=100)

        divider = ctk.CTkLabel(self.lobby_frame, text="— OR —", font=("Arial", 14), text_color="gray")
        divider.pack(pady=20)

        # Client Section
        self.ip_entry = ctk.CTkEntry(self.lobby_frame, placeholder_text="Enter Host IP (e.g., 127.0.0.1)", font=("Arial", 14), height=40)
        self.ip_entry.pack(pady=10, fill="x", padx=100)
        
        client_btn = ctk.CTkButton(self.lobby_frame, text="Connect to Session", font=("Arial", 16), height=50, command=self.start_client_thread)
        client_btn.pack(pady=10, fill="x", padx=100)
        
        self.status_label = ctk.CTkLabel(self.lobby_frame, text="", font=("Arial", 14), text_color="yellow")
        self.status_label.pack(pady=30)

    def setup_chat_screen(self):
        self.chat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        # 1. Chat History
        self.chat_history = ctk.CTkTextbox(self.chat_frame, font=("Arial", 14), state="disabled", wrap="word")
        self.chat_history.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

        # 2. Text Input Area
        input_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        input_container.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        input_container.grid_columnconfigure(0, weight=1)

        self.message_entry = ctk.CTkEntry(input_container, placeholder_text="Type a secure message...", font=("Arial", 14))
        self.message_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.message_entry.bind("<Return>", self.send_message)

        send_button = ctk.CTkButton(input_container, text="Send", font=("Arial", 14, "bold"), command=self.send_message)
        send_button.grid(row=0, column=1)

        # 3. AI Audio & Translation Controls
        self.audio_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.audio_frame.grid(row=2, column=0, pady=(0, 20))
        
        self.lang_menu = ctk.CTkOptionMenu(
            self.audio_frame, 
            values=list(self.ai_engine.SUPPORTED_LANGUAGES.keys()), 
            command=self.change_language
        )
        self.lang_menu.pack(side="left", padx=10)
        
        self.mic_button = ctk.CTkButton(
            self.audio_frame, 
            text="🎙️ Tap to Speak", 
            fg_color="#b82323", 
            hover_color="#8a1919",
            command=self.start_audio_capture
        )
        self.mic_button.pack(side="left", padx=10)

        self.auto_translate_switch = ctk.CTkSwitch(
            self.audio_frame, 
            text="Auto-Translate",
            command=self.toggle_auto_translate
        )
        self.auto_translate_switch.pack(side="left", padx=10)

    # ================= AI & AUDIO LOGIC =================

    def change_language(self, language):
        self.ai_engine.set_target_language(language)

    def toggle_auto_translate(self):
        """Properly aligned class method to flip the translation switch"""
        self.auto_translate = self.auto_translate_switch.get()

    def start_audio_capture(self):
        def _capture():
            self.mic_button.configure(state="disabled", text="Listening...", fg_color="#d4a017")
            
            text = self.ai_engine.listen_and_transcribe()
            translated = self.ai_engine.translate_text(text)
            
            if translated:
                self.message_entry.delete(0, 'end')
                self.message_entry.insert(0, translated)
            
            self.mic_button.configure(state="normal", text="🎙️ Tap to Speak", fg_color="#b82323")
            
        threading.Thread(target=_capture, daemon=True).start()

    # ================= SCREEN ROUTING =================
    
    def show_lobby(self):
        self.chat_frame.grid_forget()
        self.lobby_frame.pack(fill="both", expand=True)

    def show_chat(self):
        self.lobby_frame.pack_forget()
        self.chat_frame.grid(row=0, column=0, sticky="nsew")

    # ================= NETWORK LOGIC =================
    
    def start_server_thread(self):
        self.status_label.configure(text="Setting up Host... Waiting for friend to connect.")
        threading.Thread(target=self.host_network_logic, daemon=True).start()

    def start_client_thread(self):
        target_ip = self.ip_entry.get().strip()
        if not target_ip:
            target_ip = '127.0.0.1' 
        self.status_label.configure(text=f"Connecting to {target_ip}...")
        threading.Thread(target=self.client_network_logic, args=(target_ip,), daemon=True).start()

    def host_network_logic(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(('0.0.0.0', 2426))
            server_socket.listen(1)
            
            self.conn, address = server_socket.accept()
            self.is_host = True
            
            client_pub_key_bytes = self.conn.recv(2048)
            encrypted_aes_bytes = self.session.process_friends_public_key(client_pub_key_bytes)
            self.conn.sendall(encrypted_aes_bytes)
            
            self.transition_to_secure_chat("System: Handshake Complete! You are hosting the SECURE session.\n\n")
        except Exception as e:
            self.status_label.configure(text=f"Host Error: {e}", text_color="red")

    def client_network_logic(self, target_ip):
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((target_ip, 2426))
            
            self.conn.sendall(self.session.get_my_public_key().encode('utf-8'))
            encrypted_aes_bytes = self.conn.recv(2048)
            self.session.process_encrypted_aes_key(encrypted_aes_bytes)
            
            self.transition_to_secure_chat("System: Handshake Complete! Connected to SECURE session.\n\n")
        except Exception as e:
            self.status_label.configure(text=f"Connection Error: {e}", text_color="red")

    def transition_to_secure_chat(self, success_message):
        self.show_chat()
        self.update_chat(success_message)
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def listen_for_messages(self):
        while True:
            try:
                encrypted_received = self.conn.recv(2048)
                if not encrypted_received:
                    self.update_chat("\nSystem: The other person disconnected.\n")
                    break
                    
                plain_text = self.session.process_inbound_message(encrypted_received)
                
                # Check the switch state before displaying!
                if self.auto_translate:
                    display_text = self.ai_engine.translate_text(plain_text)
                else:
                    display_text = plain_text
                
                self.update_chat(f"Friend: {display_text}\n")
                self.ai_engine.speak(display_text)
                
            except:
                self.update_chat("\nSystem: Connection lost.\n")
                break

    def send_message(self, event=None):
        text = self.message_entry.get()
        if text.strip() == "" or not self.conn:
            return 

        self.update_chat(f"You: {text}\n")
        self.message_entry.delete(0, 'end')

        try:
            encrypted_outbound = self.session.prepare_outbound_message(text)
            self.conn.sendall(encrypted_outbound)
        except Exception as e:
            self.update_chat(f"System Error: Failed to send message ({e})\n")

    def update_chat(self, message: str):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", message)
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")

if __name__ == "__main__":
    app = SecureChatApp()
    app.mainloop()