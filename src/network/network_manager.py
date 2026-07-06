import socket
from src.security.session_manager import SecureSession

def start_server():
    port = 2426       
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(1)
    print(f"Server listening on port {port}...")

    conn, address = server_socket.accept()
    print(f"Connected to: {address}\n")

    session = SecureSession()

    try:
        print("Waiting for Client's Public Key...")
        client_pub_key_bytes = conn.recv(2048)
        
        print("Generating AES Session Key and locking it...")
        encrypted_aes_bytes = session.process_friends_public_key(client_pub_key_bytes)
        
        print("Sending locked AES key back to Client...")
        conn.sendall(encrypted_aes_bytes)
        print("Handshake Complete! Connection is now SECURE.\n")

        while True:
            encrypted_received = conn.recv(2048)
            if not encrypted_received:
                print("Client disconnected.")
                break 

            plain_text = session.process_inbound_message(encrypted_received)
            print(f"Client says: {plain_text}")

            my_reply = input("You (Server): ")
            
            encrypted_outbound = session.prepare_outbound_message(my_reply)
            conn.sendall(encrypted_outbound)
            
    except Exception as e:
        print("Connection broke or Security Error!", e)
    finally:
        conn.close()

if __name__ == "__main__":
    start_server()