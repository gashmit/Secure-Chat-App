import socket
from src.security.session_manager import SecureSession

def connect_to_server():
    target_ip = '127.0.0.1'
    target_port = 2426       
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((target_ip, target_port))
    print("Connected successfully!\n")
    
    session = SecureSession()

    try:
        print("Sending my Public Key to Server...")
        my_pub_key_str = session.get_my_public_key()
        client_socket.sendall(my_pub_key_str.encode('utf-8'))
        
        print("Waiting for Server's locked AES Key...")
        encrypted_aes_bytes = client_socket.recv(2048)
        
        print("Unlocking AES Key...")
        session.process_encrypted_aes_key(encrypted_aes_bytes)
        print("Handshake Complete! Connection is now SECURE.\n")
        
        while True:
            my_message = input("You (Client): ")
            
            encrypted_outbound = session.prepare_outbound_message(my_message)
            client_socket.sendall(encrypted_outbound)
            
            encrypted_received = client_socket.recv(2048)
            if not encrypted_received:
                print("Server disconnected.")
                break
                
            plain_text = session.process_inbound_message(encrypted_received)
            print(f"Server says: {plain_text}")
            
    except Exception as e:
        print("Connection broke or Security Error!", e)
    finally:
        client_socket.close()

if __name__ == "__main__":
    connect_to_server()