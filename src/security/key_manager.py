from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key

class RSAKeyManager:
    def __init__(self):
        """
        Task 4: The Boot Trigger.
        This constructor runs immediately when the class is initialized.
        It sets up the variables and triggers key generation.
        """
        self.private_key = None
        self.public_key = None
        
        # Trigger the generation immediately
        self.generate_keys()

    def generate_keys(self):
        """
        Task 1 & 2: Generate and Store in memory.
        Generate a 2048-bit RSA private key with a public exponent of 65537.
        Extract the public key from it.
        Assign both to self.private_key and self.public_key.
        """
        # YOUR CODE HERE
        self.private_key = rsa.generate_private_key(
            public_exponent = 65537,
            key_size = 2048,
        )
        self.public_key = self.private_key.public_key()

    def get_public_key_pem(self):
        """
        Task 3: Public Key Serialization.
        Take self.public_key and serialize it to PEM format.
        It must be encoded using SubjectPublicKeyInfo (SPKI).
        
        Returns:
            str: The public key as a UTF-8 string ready for the JSON payload.
        """
        # YOUR CODE HERE
        pem_bytes = self.public_key.public_bytes(
            encoding = serialization.Encoding.PEM,
            format = serialization.PublicFormat.SubjectPublicKeyInfo
        ) 
        return pem_bytes.decode('UTF-8')

    def encrypt_aes_key(self, aes_key: bytes, friends_public_key_data) -> bytes:
        """
        Action: 
        1. If 'friends_public_key_data' is a string, .encode('utf-8') it into bytes.
        2. Use load_pem_public_key() to turn those bytes into a usable key object.
        3. Call the .encrypt() method on that friend's key object. 
           Pass it the 'aes_key' and secure OAEP padding.
        4. Return the encrypted bytes.
        """
        # YOUR CODE HERE
        if isinstance(friends_public_key_data, str):
            friends_public_key_data = friends_public_key_data.encode('utf-8')
        
        friends_public_key_object = load_pem_public_key(friends_public_key_data)

        encrypted_result = friends_public_key_object.encrypt(
            aes_key,
            padding.OAEP(
                mgf = padding.MGF1(algorithm = hashes.SHA256()),
                algorithm = hashes.SHA256(),
                label = None
            )
        )

        return encrypted_result
        

    def decrypt_aes_key(self, encrypted_aes_key: bytes) -> bytes:
        """
        Action:
        1. Call the .decrypt() method on YOUR self.private_key.
        2. Pass it the 'encrypted_aes_key' and the exact same OAEP padding.
        3. Return the decrypted raw bytes.
        """
        # YOUR CODE HERE
        decrypted_result = self.private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf = padding.MGF1(algorithm = hashes.SHA256()),
                algorithm = hashes.SHA256(),
                label = None
            )
        )

        return decrypted_result
        

# Quick test block to run at the bottom of your file
if __name__ == "__main__":
    manager = RSAKeyManager()
    print("Keys generated successfully!")
    print(manager.get_public_key_pem())