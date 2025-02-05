import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import time
import datetime


class ChatClient:
    def __init__(self):
        print("正在初始化客户端...")
        self.window = tk.Tk()
        print("创建主窗口成功")

        # 设置主窗口在屏幕中央
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 600) // 2
        self.window.geometry(f"800x600+{x}+{y}")

        self.window.title("牛马聚集地")
        print("设置窗口属性成功")

        # 创建Socket连接
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 设置GUI
        self.setup_gui()
        print("GUI设置完成")

    def setup_gui(self):
        """设置图形界面"""
        print("开始设置GUI...")

        # 确保主窗口显示
        self.window.deiconify()

        # 登录框
        self.login_window = tk.Toplevel()
        self.login_window.title("连接到聊天室")
        self.login_window.geometry("400x400")
        self.login_window.lift()

        # 设置登录窗口在屏幕中央
        screen_width = self.login_window.winfo_screenwidth()
        screen_height = self.login_window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 400) // 2
        self.login_window.geometry(f"400x400+{x}+{y}")

        # 创建一个Frame来包含所有控件
        frame = ttk.Frame(self.login_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # 服务器地址选择
        ttk.Label(frame, text="选择连接方式:", font=('Arial', 10)).pack(anchor='w', pady=(0, 5))

        self.connect_var = tk.StringVar(value="local")
        ttk.Radiobutton(frame, text="本机测试 (localhost)", variable=self.connect_var,
                        value="local", command=self.update_server_entry).pack(anchor='w')
        ttk.Radiobutton(frame, text="连接到其他电脑", variable=self.connect_var,
                        value="remote", command=self.update_server_entry).pack(anchor='w')

        server_frame = ttk.Frame(frame)
        server_frame.pack(fill=tk.X, pady=10)
        ttk.Label(server_frame, text="服务器地址:").pack(side=tk.LEFT)
        self.server_entry = ttk.Entry(server_frame)
        self.server_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 用户名输入
        name_frame = ttk.Frame(frame)
        name_frame.pack(fill=tk.X, pady=10)
        ttk.Label(name_frame, text="你的昵称:  ").pack(side=tk.LEFT)
        self.username_entry = ttk.Entry(name_frame)
        self.username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 连接按钮
        ttk.Button(frame, text="加入聊天室", command=self.connect_to_server,
                   style='Accent.TButton').pack(pady=20)

        # 提示信息
        help_text = "提示：\n1. 确保已经有人启动了聊天服务器\n2. 如果连接其他电脑，输入对方的IP地址"
        ttk.Label(frame, text=help_text, foreground='gray').pack()

        self.update_server_entry()  # 初始化服务器地址

        # 主聊天窗口的其他控件
        self.setup_chat_window()

        # 初始化时隐藏主窗口
        self.window.withdraw()
        print("登录窗口创建成功")

    def update_server_entry(self):
        """根据选择更新服务器地址输入框"""
        if self.connect_var.get() == "local":
            self.server_entry.delete(0, tk.END)
            self.server_entry.insert(0, "localhost")
            self.server_entry.config(state='disabled')
        else:
            self.server_entry.config(state='normal')
            self.server_entry.delete(0, tk.END)

    def setup_chat_window(self):
        """设置主聊天窗口的控件"""
        # 聊天记录区域
        self.chat_frame = ttk.Frame(self.window)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建文本框
        self.chat_text = tk.Text(self.chat_frame, height=20, wrap=tk.WORD)
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        # 配置颜色标签
        self.chat_text.tag_configure('newest', foreground='red')
        self.chat_text.tag_configure('second_newest', foreground='green')

        # 存储最后两条消息的位置
        self.last_position = None
        self.second_last_position = None

        # 输入区域
        self.input_frame = ttk.Frame(self.window)
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.message_entry = ttk.Entry(self.input_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", self.handle_return)

        self.send_button = ttk.Button(self.input_frame, text="发送", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.file_button = ttk.Button(self.input_frame, text="发送文件", command=self.send_file)
        self.file_button.pack(side=tk.LEFT)

    def connect_to_server(self):
        """连接到服务器"""
        try:
            server_address = self.server_entry.get()
            self.username = self.username_entry.get()

            if not self.username:
                messagebox.showerror("错误", "请输入用户名")
                return

            # 创建新的socket连接
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_address, 5000))

            # 发送用户名并等待验证
            while True:
                self.client_socket.send(self.username.encode())
                response = self.client_socket.recv(1024).decode()

                if response == "USERNAME_ACCEPTED":
                    break
                elif response == "USERNAME_TAKEN":
                    new_username = self.handle_username_taken()
                    if not new_username:  # 用户取消了输入
                        self.client_socket.close()
                        self.client_socket = None
                        return
                    self.username = new_username
                else:
                    raise Exception("未知的服务器响应")

            # 开启接收消息的线程
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            self.login_window.destroy()
            self.window.deiconify()  # 显示主窗口

        except Exception as e:
            messagebox.showerror("错误", f"连接失败: {str(e)}")
            if self.client_socket:
                try:
                    self.client_socket.close()
                    self.client_socket = None
                except:
                    pass

    def send_message(self):
        """发送文本消息"""
        message = self.message_entry.get()
        if message:
            try:
                # 添加当前时间
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                data = json.dumps({
                    'type': 'text',
                    'content': message,
                    'time': current_time
                })
                self.client_socket.send(data.encode())
                self.message_entry.delete(0, tk.END)
            except:
                messagebox.showerror("错误", "发送消息失败")

    def send_file(self):
        """发送文件"""
        filename = filedialog.askopenfilename()
        if filename:
            try:
                filesize = os.path.getsize(filename)
                current_time = datetime.datetime.now().strftime("%H:%M:%S")

                # 修改为1GB限制
                if filesize > 1024 * 1024 * 1024:  # 1GB限制
                    messagebox.showerror("错误", "文件太大，请选择小于1GB的文件")
                    return

                data = json.dumps({
                    'type': 'file',
                    'filename': os.path.basename(filename),
                    'filesize': filesize,
                    'time': current_time
                })
                self.client_socket.send(data.encode())

                time.sleep(0.1)

                # 添加初始进度显示
                self.append_message("\n")
                progress_line = self.chat_text.index('end-2c linestart')

                with open(filename, 'rb') as f:
                    bytes_sent = 0
                    while bytes_sent < filesize:
                        chunk = f.read(min(1024, filesize - bytes_sent))
                        if not chunk:
                            break
                        self.client_socket.send(chunk)
                        bytes_sent += len(chunk)

                        # 更新进度条
                        progress = (bytes_sent / filesize) * 100
                        progress_text = f"\r发送: {self.create_progress_bar(progress)}"

                        # 更新进度显示
                        self.chat_text.delete(progress_line, f"{progress_line} lineend")
                        self.chat_text.insert(progress_line, progress_text)
                        self.chat_text.see(progress_line)

                # 显示100%进度
                final_progress_text = f"\r发送: {self.create_progress_bar(100.0)}\n"
                self.chat_text.delete(progress_line, f"{progress_line} lineend")
                self.chat_text.insert(progress_line, final_progress_text)

                # 直接添加完成消息
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                self.append_message(f"[{current_time}] 文件 {os.path.basename(filename)} 发送成功")

            except ConnectionError:
                messagebox.showerror("错误", "连接断开，文件发送失败")
            except Exception as e:
                messagebox.showerror("错误", f"发送文件失败: {str(e)}")

    def receive_messages(self):
        """接收消息"""
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if not data:
                    break

                try:
                    message = json.loads(data)
                    if message['type'] == 'file_notification':
                        self.handle_incoming_file(message)
                    else:
                        self.append_message(data)
                except json.JSONDecodeError:
                    self.append_message(data)

            except:
                break

        messagebox.showinfo("提示", "与服务器的连接已断开")
        self.window.quit()

    def handle_incoming_file(self, message):
        """处理接收到的文件"""
        sender = message['sender']
        filename = message['filename']
        filesize = message['filesize']

        if messagebox.askyesno("文件接收", f"是否接收来自 {sender} 的文件 {filename}?"):
            try:
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".*",
                    initialfile=filename
                )

                if not save_path:  # 用户取消了保存对话框
                    # 丢弃接收到的文件数据
                    self.discard_file_data(filesize)
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    self.append_message(f"[{current_time}] 已取消接收文件 {filename}")
                    return

                self.receive_file_data(save_path, filename, filesize)

            except Exception as e:
                messagebox.showerror("错误", f"接收文件失败: {str(e)}")
                # 出现错误时也需要丢弃剩余的文件数据
                self.discard_file_data(filesize)
        else:
            # 用户拒绝接收文件
            self.discard_file_data(filesize)
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.append_message(f"[{current_time}] 已拒绝接收文件 {filename}")

    def append_message(self, message):
        """添加消息到聊天记录"""
        # 清除之前的颜色标签
        self.chat_text.tag_remove('newest', '1.0', 'end')
        self.chat_text.tag_remove('second_newest', '1.0', 'end')

        # 记录新消息的开始位置
        start_pos = self.chat_text.index('end-1c')

        # 插入新消息
        self.chat_text.insert('end', message + '\n')

        # 记录新消息的结束位置
        end_pos = self.chat_text.index('end-1c')

        # 如果存在上一条消息的位置，将其标记为绿色
        if self.last_position:
            last_start, last_end = self.last_position
            self.chat_text.tag_add('second_newest', last_start, last_end)

        # 更新位置记录
        self.second_last_position = self.last_position if self.last_position else None
        self.last_position = (start_pos, end_pos)

        # 将新消息标记为红色
        self.chat_text.tag_add('newest', start_pos, end_pos)

        # 滚动到最新消息
        self.chat_text.see('end')

    def handle_return(self, event):
        """处理回车键事件"""
        if self.message_entry.get().strip():  # 确保输入框不为空
            self.send_message()

    def create_progress_bar(self, progress):
        """创建进度条字符串"""
        width = 30  # 进度条总长度
        filled = int(width * progress / 100)  # 已完成的长度
        bar = '=' * filled + '>' + '-' * (width - filled - 1)
        return f"[{bar}] {progress:.1f}%"

    def handle_username_taken(self):
        """处理用户名被占用的情况"""
        while True:
            new_username = simpledialog.askstring(
                "用户名已被使用",
                "该用户名已被使用，请输入新的用户名：",
                parent=self.login_window
            )

            if new_username is None:  # 用户点击取消或关闭对话框
                return None

            if not new_username.strip():  # 用户输入空字符串
                messagebox.showerror("错误", "用户名不能为空")
                continue

            return new_username.strip()

    def discard_file_data(self, filesize):
        """丢弃文件数据"""
        try:
            received_size = 0
            while received_size < filesize:
                chunk_size = min(1024, filesize - received_size)
                chunk = self.client_socket.recv(chunk_size)
                if not chunk:
                    break
                received_size += len(chunk)
        except Exception as e:
            print(f"丢弃文件数据时出错: {e}")

    def receive_file_data(self, save_path, filename, filesize):
        """接收文件数据并保存"""
        try:
            # 添加初始进度显示
            self.append_message("\n")
            progress_line = self.chat_text.index('end-2c linestart')

            with open(save_path, 'wb') as f:
                received_size = 0
                while received_size < filesize:
                    chunk = self.client_socket.recv(min(1024, filesize - received_size))
                    if not chunk:
                        raise Exception("连接断开")
                    f.write(chunk)
                    received_size += len(chunk)

                    # 更新进度条
                    progress = (received_size / filesize) * 100
                    progress_text = f"\r接收: {self.create_progress_bar(progress)}"

                    # 更新进度显示
                    self.chat_text.delete(progress_line, f"{progress_line} lineend")
                    self.chat_text.insert(progress_line, progress_text)
                    self.chat_text.see(progress_line)

            # 显示100%进度
            final_progress_text = f"\r接收: {self.create_progress_bar(100.0)}\n"
            self.chat_text.delete(progress_line, f"{progress_line} lineend")
            self.chat_text.insert(progress_line, final_progress_text)

            # 直接添加完成消息
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.append_message(f"[{current_time}] 文件 {filename} 接收完成")

        except Exception as e:
            messagebox.showerror("错误", f"接收文件失败: {str(e)}")
            try:
                os.remove(save_path)
            except:
                pass

    def run(self):
        """运行客户端"""
        self.window.mainloop()


if __name__ == "__main__":
    print("程序开始运行...")
    try:
        client = ChatClient()
        print("客户端创建成功，开始运行...")
        client.run()
    except Exception as e:
        print(f"发生错误: {e}")
        input("按回车键退出...")