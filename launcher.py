import tkinter as tk
from tkinter import ttk
import socket
import threading
import sys
import os
from server import ChatServer


class ServerLauncher:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("聊天服务器启动器")
        self.window.geometry("800x650")

        # 居中显示
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 650) // 2
        self.window.geometry(f"800x650+{x}+{y}")

        self.setup_gui()

    def setup_gui(self):
        frame = ttk.Frame(self.window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        ttk.Label(frame, text="聊天服务器启动器",
                  font=('Simsun', 16, 'bold')).pack(pady=(0, 20))

        # 服务器信息显示
        self.info_frame = ttk.LabelFrame(frame, text="服务器信息", padding="10")
        self.info_frame.pack(fill=tk.X, pady=10)

        # 获取本机IP
        local_ip = self.get_local_ip()
        ttk.Label(self.info_frame, text=f"本机IP: {local_ip}").pack(anchor='w')
        ttk.Label(self.info_frame, text="端口: 5000").pack(anchor='w')

        # 状态显示
        self.status_var = tk.StringVar(value="未启动")
        ttk.Label(frame, text="状态: ").pack(anchor='w', pady=(20, 0))
        ttk.Label(frame, textvariable=self.status_var,
                  font=('Simsun', 10, 'bold')).pack(anchor='w')

        # 在线用户信息
        self.users_frame = ttk.LabelFrame(frame, text="在线用户信息", padding="10")
        self.users_frame.pack(fill=tk.BOTH, pady=10)

        # 在线人数显示
        self.online_count_var = tk.StringVar(value="当前在线人数: 0")
        ttk.Label(self.users_frame, textvariable=self.online_count_var,
                  font=('Simsun', 10, 'bold')).pack(anchor='w', pady=(0, 10))

        # 创建一个固定高度的Frame来容纳Treeview
        tree_frame = ttk.Frame(self.users_frame)
        tree_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        # 创建用户列表显示（使用Treeview）
        self.user_tree = ttk.Treeview(tree_frame,
                                      columns=('username', 'ip', 'port', 'time'),
                                      show='headings',
                                      height=6)

        # 设置列标题
        self.user_tree.heading('username', text='用户昵称')
        self.user_tree.heading('ip', text='IP地址')
        self.user_tree.heading('port', text='端口')
        self.user_tree.heading('time', text='加入时间')

        # 设置列宽
        self.user_tree.column('username', width=120)
        self.user_tree.column('ip', width=120)
        self.user_tree.column('port', width=80)
        self.user_tree.column('time', width=160)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scrollbar.set)

        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 启动按钮
        self.start_button = ttk.Button(frame, text="启动服务器",
                                       command=self.start_server)
        self.start_button.pack(pady=20)

        # 提示信息
        help_text = ("使用说明：\n"
                     "1. 点击'启动服务器'按钮启动\n"
                     "2. 将本机IP告诉其他用户\n"
                     "3. 其他用户在客户端输入此IP即可连接")
        ttk.Label(frame, text=help_text, foreground='gray').pack()

    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def update_user_info(self, user_count, user_list):
        """更新用户信息显示"""

        # 在主线程中更新UI
        def update():
            # 更新在线人数
            self.online_count_var.set(f"当前在线人数: {user_count}")

            # 清空现有显示
            for item in self.user_tree.get_children():
                self.user_tree.delete(item)

            # 添加用户信息
            for user in user_list:
                self.user_tree.insert('', 'end',
                                      values=(user['username'],
                                              user['ip'],
                                              user['port'],
                                              user['join_time']))

        # 确保在主线程中更新UI
        self.window.after(0, update)

    def start_server(self):
        """启动服务器"""
        self.start_button.config(state='disabled')
        self.status_var.set("正在启动...")

        # 在新线程中启动服务器
        def run_server():
            try:
                server = ChatServer()
                server.set_info_callback(self.update_user_info)
                self.window.after(100, lambda: self.status_var.set("运行中"))
                server.start()
            except Exception as e:
                self.window.after(100, lambda: self.status_var.set(f"启动失败: {e}"))
                self.window.after(100, lambda: self.start_button.config(state='normal'))

        threading.Thread(target=run_server, daemon=True).start()

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    launcher = ServerLauncher()
    launcher.run()