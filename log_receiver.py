import socket
import os
import threading
import datetime

class LogServer:
    def __init__(self, host, port, tag_path_file):
        self.host = host
        self.port = port
        self.tag_path_file = tag_path_file
        self.tag_paths = self.load_tag_paths()

    def load_tag_paths(self):
        """从指定文件中加载标签路径到字典中。"""
        with open(self.tag_path_file, 'r') as file:
            paths = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in file.readlines()}
        return paths

    def handle_client_connection(self, conn, addr):
        """处理客户端连接的独立线程。"""
        print(f"与 {addr} 建立了连接。")
        buffer = ""
        try:
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break
                print(f"从 {addr} 接收到数据: {data}")
                buffer += data

                while '&!LOGEND!&' in buffer:
                    complete_message, _, buffer = buffer.partition('&!LOGEND!&')
                    #print(f"处理完整消息：{complete_message}")
                    self.process_message(complete_message)
        except ConnectionResetError:
            print(f"连接 {addr} 被重置。")
        finally:
            conn.close()
            print(f"已关闭与 {addr} 的连接。")

    def process_message(self, tag_message):
        """处理并保存带标签的消息。"""
        parts = tag_message.split('&!BCTCLOG!&', 1)
        if len(parts) > 1:
            tag_part, message = parts
            for tag, file_path in self.tag_paths.items():
                if tag_part.strip().startswith(tag):
                    self.save_message(message.strip(), file_path)
                    #print(f"已保存消息到 {file_path}")
                    return
        print(f"无法找到有效标签或格式不正确：{tag_message}")

    def save_message(self, message, file_path):
        """将消息保存到指定的文件路径。"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'a') as logfile:
                logfile.write(f"{message}\n")
        except Exception as e:
            print(f"写入文件 {file_path} 失败: {e}")

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            print(f"监听中 {self.host}:{self.port}")

            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client_connection, args=(conn, addr)).start()

if __name__ == "__main__":
    server = LogServer('0.0.0.0', 9900, 'tag_paths.txt')
    server.start_server()
