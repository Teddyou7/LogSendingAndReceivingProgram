import socket
import sys
import time
import os
import re
import chardet

#日志发送程序
#启动命令
#\log_sender.py server=42.193.48.240:9999 file=".\SquadGame.log"  tag=test

#或同级配置文件
#log_sender.cfg
#
#server=42.193.48.240:9999
#file=".\SquadGame.log"
#tag=test

class LogSender:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.connection = None

    def ensure_connected(self):
        if self.connection is None:
            try:
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((self.server_ip, self.server_port))
            except socket.error as e:
                print(f"Failed to connect: {e}")
                self.connection = None

    def send(self, message):
        self.ensure_connected()
        if self.connection:
            try:
                self.connection.sendall(message)  # 这里的 message 应该已经是 bytes 类型
                return True
            except socket.error as e:
                print(f"Send failed: {e}")
                self.connection.close()
                self.connection = None
        return False

def load_config(cfg_path):
    config = {}
    if os.path.exists(cfg_path):
        with open(cfg_path, 'r') as cfg_file:
            for line in cfg_file:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

def should_send(message):
    # 定义正则表达式规则
    rules = [
        r"Die\(\):\ Player:(.+)\ KillingDamage=([0-9.]+)\ from\ .*\ steam:\ ([0-9]+)\ \|\ .*\)\ caused\ by\ BP_(.+)_C_",
        r"\[([0-9]{4}\.[0-9]{2}\.[0-9]{2}-[0-9]{2}\.[0-9]{2}\.[0-9]{2}):([0-9]{3})\].*LogSquad:\ (.+?)\ \(.*steam:\ ([0-9]+)\).*created\ Squad\ ([0-9]+)\ \(Squad\ Name:\ (.+?)\)\ on\ (.+)$",
        r"NewPlayer.*\ \(IP:\ ([0-9.]+)\ \|\ Online\ IDs:\ EOS:\ ([0-9a-z]+)\ steam:\ ([0-9]+)\)",
        r"StartLoadingDestination",
        r"LogSquadGameEvents",
        r"Wound\(\):\ Player:(.+)\ KillingDamage=([0-9.]+)\ from\ .*\ steam:\ ([0-9]+)\ .*caused\ by\ BP_(.+)_C",
        r"Player:(.+)\ ActualDamage=([0-9.]+)\ from\ (.+)\ \(Online\ .*\ steam:\ ([0-9]+)\ .*caused\ by\ BP_(.+)_C",
        r"\[([0-9]{4}\.[0-9]{2}\.[0-9]{2}-[0-9]{2}\.[0-9]{2}\.[0-9]{2}):([0-9]{3})].*StartLoadingDestination\ to:\ .*\/([A-Za-z0-9_]+)",
        r"\[([0-9]{4}\.[0-9]{2}\.[0-9]{2}-[0-9]{2}\.[0-9]{2}\.[0-9]{2}):([0-9]{3})\]\[.+\]LogSquad\:\ (.+)\ \(.*steam:\ ([0-9]+)\)\ has\ revived\ (.+)\ \(.*steam:\ ([0-9]+)\)",
        r"Possess",
        r"LogSquadTrace"
    ]

    for rule in rules:
        if re.search(rule, message):
            return True  # 如果消息匹配任何一个规则，返回True

    return False  # 如果消息不匹配任何规则，返回False

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(4096)  # 读取文件的前4096字节来猜测字符集
    result = chardet.detect(raw_data)
    return result['encoding']

def monitor_and_send_data(sender, file_path, tag):
    position = 0
    initial_run = True
    encoding = 'utf-8'  # 默认字符集
    while True:
        try:
            if not os.path.exists(file_path):
                print(f"File {file_path} does not exist. Waiting for it to appear...")
                position = 0
                initial_run = True
                time.sleep(1)
                continue

            if initial_run:
                encoding = detect_encoding(file_path)  # 检测文件字符集
                print(f"Detected encoding: {encoding}")
                position = os.path.getsize(file_path)
                initial_run = False

            current_size = os.path.getsize(file_path)
            if position > current_size:
                print("File was truncated or reset. Starting from the beginning of the new file.")
                position = 0
                encoding = detect_encoding(file_path)  # 重新检测字符集，因为文件可能已经改变

            with open(file_path, 'r', encoding=encoding, errors='replace') as file:
                file.seek(position)
                line = file.readline()
                while line:
                    if should_send(line):
                        full_message = f"{tag}&!BCTCLOG!&{line.strip()}"
                        if sender.send(full_message.encode('utf-8')):
                            print(f"Send=Put, Tag={tag}, Content={line.strip()}")
                        else:
                            print("Send=Failed, skipping line after retry.")
                    else:
                        print(f"Send=Skipped, Tag={tag}, Content={line.strip()}")
                    position = file.tell()
                    line = file.readline()
                time.sleep(0.05)
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(1)

if __name__ == "__main__":
    print("==============================================")
    print("")
    print("              Bugle Call To Charge")
    print("            由冲锋号社区提供技术支持")
    print("               QQ群：703511605")
    print("")
    print("      请修改log_sender.cfg或使用参数启动")
    print(" 请将本程序与配置文件放置在游戏日志同级路径下")
    print("")
    print("==============================================")
    print("当前使用程序版本号：1.0.4-240312")
    print("启动参数: ./log_sender server=192.168.1.1:6900 file=SquadGameFile tag=Squad")
    print("如果您未使用参数启动，则将会读取同级路径下的配置文件：log_sender.cfg")
    print("")
    print("如果在配置文件中未找到参数，则默认参数如下：")
    print("server=localhost:6900")
    print("file=SquadGame.log")
    print("tag=default")
    print("")
    print("  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *")
    print("")
    time.sleep(3)
    cfg_path = "log_sender.cfg"
    config = load_config(cfg_path)

    args = {arg.split('=')[0]: arg.split('=')[1] for arg in sys.argv[1:]}
    server = args.get('server', config.get('server', 'localhost:6900')).split(':')
    file_path = args.get('file', config.get('file', 'SquadGame.log'))
    tag = args.get('tag', config.get('tag', 'default'))

    sender = LogSender(server[0], int(server[1]))
    monitor_and_send_data(sender, file_path, tag)
