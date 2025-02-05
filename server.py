import socket
import threading
import json
import os
import datetime


class ChatServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}  # 存储客户端连接 {client_socket: username}
        self.usernames = set()  # 存储当前在线的用户名
        self.user_info = {}  # 存储用户详细信息 {username: {'ip': ip, 'port': port, 'join_time': time}}
        self.info_callback = None  # 用于更新UI的回调函数

    def start(self):
        # 添加 socket 重用选项
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"服务器启动成功，监听地址: {self.host}:{self.port}")

        while True:
            client_socket, address = self.server_socket.accept()
            print(f"新的连接来自: {address}")

            # 开启新线程处理客户端连接
            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket, address)
            )
            client_thread.start()

    def check_username(self, username):
        """检查用户名是否可用"""
        if not username or not username.strip():
            return False
        return username not in self.usernames

    def handle_client(self, client_socket, client_address):
        try:
            # 接收并验证用户名
            while True:
                try:
                    username = client_socket.recv(1024).decode()
                    if not username:  # 连接已关闭
                        return

                    if self.check_username(username):
                        # 用户名可用
                        client_socket.send("USERNAME_ACCEPTED".encode())
                        self.clients[client_socket] = username
                        self.usernames.add(username)
                        # 记录用户信息
                        self.user_info[username] = {
                            'ip': client_address[0],
                            'port': client_address[1],
                            'join_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        self.update_user_info()  # 更新UI显示
                        break
                    else:
                        # 用户名已被使用或无效
                        client_socket.send("USERNAME_TAKEN".encode())
                except Exception as e:
                    print(f"用户名验证过程出错: {e}")
                    return

            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.broadcast(f"[{current_time}] {username} 加入了聊天室")

            # 添加文件传输状态标志
            is_receiving_file = False
            remaining_bytes = 0

            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                if is_receiving_file:
                    # 正在接收文件内容
                    try:
                        remaining_bytes -= len(data)
                        # 转发文件数据给接收方
                        for client in self.clients:
                            if client != client_socket:
                                try:
                                    client.send(data)
                                except:
                                    continue

                        if remaining_bytes <= 0:
                            is_receiving_file = False
                    except Exception as e:
                        print(f"文件传输错误: {e}")
                        is_receiving_file = False
                else:
                    # 尝试解析普通消息
                    try:
                        message = json.loads(data.decode())
                        if message['type'] == 'text':
                            self.broadcast(f"[{message['time']}] {username}: {message['content']}")
                        elif message['type'] == 'file':
                            # 设置文件传输状态
                            is_receiving_file = True
                            remaining_bytes = message['filesize']
                            self.handle_file_transfer(client_socket, username, message)
                    except json.JSONDecodeError:
                        print("无法解析的消息格式")
                        continue


        except Exception as e:

            print(f"处理客户端时出错: {e}")

        finally:

            if client_socket in self.clients:
                username = self.clients[client_socket]

                self.usernames.remove(username)

                del self.user_info[username]  # 移除用户信息

                current_time = datetime.datetime.now().strftime("%H:%M:%S")

                del self.clients[client_socket]

                self.broadcast(f"[{current_time}] {username} 离开了聊天室")

                self.update_user_info()  # 更新UI显示

                client_socket.close()

    def handle_file_transfer(self, sender_socket, username, message):
        """处理文件传输"""
        filename = message['filename']
        filesize = message['filesize']
        time = message['time']

        # 通知其他客户端有新文件可以接收
        notification = json.dumps({
            'type': 'file_notification',
            'sender': username,
            'filename': filename,
            'filesize': filesize,
            'time': time
        })

        # 向其他客户端广播文件通知
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(notification.encode())
                except:
                    continue

    def broadcast(self, message):
        """广播消息给所有客户端"""
        for client in self.clients:
            try:
                client.send(message.encode())
            except:
                continue

    def broadcast_except_sender(self, message, sender_socket):
        """广播消息给除了发送者以外的所有客户端"""
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(message.encode())
                except:
                    continue

    def set_info_callback(self, callback):
        """设置信息更新回调函数"""
        self.info_callback = callback

    def update_user_info(self):
        """更新用户信息"""
        if self.info_callback:
            user_list = []
            for username, info in self.user_info.items():
                user_list.append({
                    'username': username,
                    'ip': info['ip'],
                    'port': info['port'],
                    'join_time': info['join_time']
                })
            self.info_callback(len(self.clients), user_list)


if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
    except Exception as e:
        print(f"服务器启动失败: {e}")