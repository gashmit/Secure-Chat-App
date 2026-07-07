import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class CryptoEngine:
    def __init__(self):
        self.aes_session_key = None

    def encrypt_message(self, plaintext_message: str):
        """
        Takes a string message and encrypts it using self.aes_session_key.
        
        Requirements:
        1. Generate a random 12-byte nonce (Initialization Vector).
        2. Use AES-GCM mode.
        3. Return BOTH the ciphertext and the nonce (your friends will 
           need the nonce to decrypt it on the other side).
        """
        # YOUR CODE HERE
        data = plaintext_message.encode('utf-8')
        
        nonce = os.urandom(12)

        cipher = Cipher(algorithms.AES(self.aes_session_key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        
        ct = encryptor.update(data) + encryptor.finalize()
        tag = encryptor.tag

        return nonce + tag + ct




    def decrypt_message( self, combined_data: bytes):
        """
        Takes the encrypted bytes and the nonce received from the network,
        and decrypts it back into a readable string using self.aes_session_key.
        """
        # YOUR CODE HERE
        nonce = combined_data[:12]
        tag = combined_data[12:28]
        ct = combined_data[28:]
        
        cipher = Cipher(algorithms.AES(self.aes_session_key), modes.GCM(nonce,  tag))
        decryptor = cipher.decryptor()
        
        plaintext = decryptor.update(ct) + decryptor.finalize()
        return plaintext.decode('utf-8')

if __name__ == "__main__":
    print("--- Starting AES-GCM Encryption Test ---")
    
    # 1. Initialize your engine
    engine = CryptoEngine()
    
    # 2. Manually set a dummy session key for testing
    # (In the real app, this will be set during the RSA handshake)
    engine.aes_session_key = os.urandom(32) 
    
    # 3. Create a test message
    original_message = "This is a top-secret DRDO message."
    print(f"Original Text: {original_message}")
    
    # 4. Encrypt it
    encrypted_payload = engine.encrypt_message(original_message)
    print(f"Encrypted Payload (Hex): {encrypted_payload.hex()}")
    
    # 5. Decrypt it
    decrypted_text = engine.decrypt_message(encrypted_payload)
    print(f"Decrypted Text: {decrypted_text}")
    
    # 6. Verify success
    if original_message == decrypted_text:
        print("\nSUCCESS: The engine successfully encrypted and decrypted the payload!")
    else:
        print("\nFAILURE: The messages do not match.")