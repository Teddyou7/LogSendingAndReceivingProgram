import socket
import os
import threading

#日志接收程序
#[root@cd3 log_receiver]# cat tag_paths.txt 
#default=./logs
#test=/Jackets/log_receiver/123.log
#ted=/Jackets/log_receiver/1211.log


def load_tag_paths(tag_path_file):
    """Load tag paths from the given file into a dictionary."""
    with open(tag_path_file, 'r') as file:
        return {line.split('=')[0]: line.split('=')[1].strip() for line in file.readlines()}

def handle_client_connection(conn, addr, tag_paths):
    """Handle the client connection in a separate thread."""
    print(f"Connected by {addr}")
    buffer = ""
    try:
        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break
            buffer += data

            # Handle complete messages in the buffer
            while '&!BCTCLOG!&' in buffer:
                if '&!BCTCLOG!&' in buffer:
                    tag_message, _, buffer = buffer.partition('&!BCTCLOG!&')
                    process_message(tag_message, tag_paths)
    except ConnectionResetError:
        print(f"Connection reset by {addr}")
    finally:
        conn.close()

def process_message(tag_message, tag_paths):
    """Process and save the tagged message."""
    # Attempt to find the last occurrence of any tag in the message
    for tag, file_path in tag_paths.items():
        if tag_message.endswith(tag):
            message = tag_message[:-len(tag)].strip()
            save_message(tag, message, file_path)
            return
    print(f"Unable to find a valid tag for message: {tag_message}")

def save_message(tag, message, file_path):
    """Save the message to the specified file path."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'a') as logfile:
        logfile.write(message + '\n')

def start_server(host, port, tag_path_file):
    tag_paths = load_tag_paths(tag_path_file)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        print(f"Listening on {host}:{port}")

        while True:
            conn, addr = s.accept()
            # Start a new thread for each connection
            client_thread = threading.Thread(target=handle_client_connection, args=(conn, addr, tag_paths))
            client_thread.start()

if __name__ == "__main__":
    host = '0.0.0.0'
    port = 9900
    tag_path_file = 'tag_paths.txt'
    start_server(host, port, tag_path_file)
