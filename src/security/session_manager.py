from cryptography import exceptions
import os
from src.security.key_manager import RSAKeyManager
from src.security.crypto import CryptoEngine

class SecureSession:
    def __init__(self):
        # HINT: Instantiate your KeyManager and CryptoEngine here.
        # HINT: Create a boolean variable like 'self.is_ready = False' 
        # to track if the handshake is finished.
        self.rsa = RSAKeyManager()
        self.cryeng = CryptoEngine()

        self.is_ready = False

    # ==========================================
    # PHASE 1: THE HANDSHAKE
    # ==========================================

    def get_my_public_key(self) -> bytes:
        """
        Action: Call the method from your RSA engine that exports the public key.
        Return: The public key bytes so the network guy can send it.
        """
        return self.rsa.get_public_key_pem()


    def process_friends_public_key(self, friends_pub_key_bytes: bytes) -> bytes:
        """
        Scenario: The network guy receives the friend's public key and passes it here.
        Action: 
        1. Generate a random 32-byte AES key using os.urandom.
        2. Set this new key into your CryptoEngine instance.
        3. Encrypt this AES key using the friend's public key (using your RSA engine).
        4. Set self.is_ready = True.
        Return: The encrypted AES key bytes so the network guy can send it back.
        """
        aes_key = os.urandom(32)

        self.cryeng.aes_session_key = aes_key

        encrypted_aes_key_bytes = self.rsa.encrypt_aes_key(aes_key, friends_pub_key_bytes)

        self.is_ready = True

        return encrypted_aes_key_bytes







    def process_encrypted_aes_key(self, encrypted_aes_key_bytes: bytes):
        """
        Scenario: The network guy receives the wrapped AES key and passes it here.
        Action:
        1. Decrypt the AES key using your RSA engine's private key.
        2. Set that decrypted AES key into your CryptoEngine instance.
        3. Set self.is_ready = True.
        """
        decrypted_aes_key_bytes = self.rsa.decrypt_aes_key(encrypted_aes_key_bytes)
        self.cryeng.aes_session_key = decrypted_aes_key_bytes
        self.is_ready = True
    # ==========================================
    # PHASE 2: THE CHAT
    # ==========================================

    def prepare_outbound_message(self, text: str) -> bytes:
        """
        Action: Check if self.is_ready is True (raise an error if not).
        Then, pass the text to your CryptoEngine's encrypt method and return the bytes.
        """
        if(self.is_ready == False):
            raise Exception("Security Error: Handshake is not comeplete!")
        
        return self.cryeng.encrypt_message(text)


    def process_inbound_message(self, data: bytes) -> str:
        """
        Action: Check if self.is_ready is True.
        Then, pass the bytes to your CryptoEngine's decrypt method and return the string.
        """
        if(self.is_ready == False):
            raise Exception("Security Error: Handshake is not complete!")

        decrypted_message = self.cryeng.decrypt_message(data)
        return decrypted_message

if __name__ == "__main__":
    # 1. Boot up two clients
    alice = SecureSession()
    bob = SecureSession()

    print("Status: Initiating Handshake...")
    
    # 2. The Handshake
    # Alice sends her public key to Bob
    alice_public_key = alice.get_my_public_key()
    
    # Bob generates the AES key, locks it with Alice's public key, and sends it back
    encrypted_aes_key = bob.process_friends_public_key(alice_public_key)
    
    # Alice unlocks it with her private key
    alice.process_encrypted_aes_key(encrypted_aes_key)
    
    print(f"Alice Ready? {alice.is_ready}")
    print(f"Bob Ready? {bob.is_ready}")
    print("\nStatus: Handshake Complete. Entering Chat Phase...\n")

    # 3. The Chat
    secret_message = "Hello Bob! We are completely invisible to the network."
    print(f"Alice sends: {secret_message}")
    
    # Alice encrypts
    ciphertext = alice.prepare_outbound_message(secret_message)
    print(f"Network sees: {ciphertext[:30]}... (Gibberish!)")
    
    # Bob decrypts
    decrypted_text = bob.process_inbound_message(ciphertext)
    print(f"Bob reads: {decrypted_text}")