import customtkinter as ctk
import socket
import threading
from src.security.session_manager import SecureSession

# Set the overall theme and color
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SecureChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Secure E2EE Chat")
        self.geometry("600x700")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Network State
        self.conn = None # Will hold the active socket (either server's client connection or client's server connection)
        self.session = SecureSession()
        self.is_host = False

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

        self.chat_history = ctk.CTkTextbox(self.chat_frame, font=("Arial", 14), state="disabled", wrap="word")
        self.chat_history.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

        input_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        input_container.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        input_container.grid_columnconfigure(0, weight=1)

        self.message_entry = ctk.CTkEntry(input_container, placeholder_text="Type a secure message...", font=("Arial", 14))
        self.message_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.message_entry.bind("<Return>", self.send_message)

        send_button = ctk.CTkButton(input_container, text="Send", font=("Arial", 14, "bold"), command=self.send_message)
        send_button.grid(row=0, column=1)

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
            target_ip = '127.0.0.1' # Default to local testing
        self.status_label.configure(text=f"Connecting to {target_ip}...")
        threading.Thread(target=self.client_network_logic, args=(target_ip,), daemon=True).start()

    def host_network_logic(self):
        """The exact logic from your network_manager.py, adapted for UI"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(('0.0.0.0', 2426))
            server_socket.listen(1)
            
            self.conn, address = server_socket.accept()
            self.is_host = True
            
            # Handshake
            client_pub_key_bytes = self.conn.recv(2048)
            encrypted_aes_bytes = self.session.process_friends_public_key(client_pub_key_bytes)
            self.conn.sendall(encrypted_aes_bytes)
            
            self.transition_to_secure_chat("System: Handshake Complete! You are hosting the SECURE session.\n\n")
        except Exception as e:
            self.status_label.configure(text=f"Host Error: {e}", text_color="red")

    def client_network_logic(self, target_ip):
        """The exact logic from your test_client.py, adapted for UI"""
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((target_ip, 2426))
            
            # Handshake
            self.conn.sendall(self.session.get_my_public_key().encode('utf-8'))
            encrypted_aes_bytes = self.conn.recv(2048)
            self.session.process_encrypted_aes_key(encrypted_aes_bytes)
            
            self.transition_to_secure_chat("System: Handshake Complete! Connected to SECURE session.\n\n")
        except Exception as e:
            self.status_label.configure(text=f"Connection Error: {e}", text_color="red")

    def transition_to_secure_chat(self, success_message):
        """Swaps the UI and starts the listening loop"""
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
                self.update_chat(f"Friend: {plain_text}\n")
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