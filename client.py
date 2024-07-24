print("Starting the program...")
import tkinter as tk
print("Tkinter imported successfully")
from tkinter import ttk
from PIL import Image, ImageTk
print("PIL imported successfully")
from tkinter import filedialog
from tkinter import messagebox
import socket
import pickle
import struct
import os
import threading
from datetime import datetime

import tkinter as tk

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class FirstScreen(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Computer Science Chat App")
        self.configure(bg="#f0f0f0")

        icon_path = os.path.join(os.path.dirname(__file__), 'images', 'chatapp_ca.ico')
        self.iconbitmap(icon_path)

        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        self.x_co = int((screen_width / 2) - (550 / 2))  
        self.y_co = int((screen_height / 2) - (400 / 2)) - 80 
        self.geometry(f"550x400+{self.x_co}+{self.y_co}")  

        self.user = None
        self.image_extension = None
        self.image_path = None

        self.first_frame = tk.Frame(self, bg="#f0f0f0")
        self.first_frame.pack(fill="both", expand=True)

        self.user_image = 'images/user.png'

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TButton",
                             background="#3498db",
                             foreground="white",
                             font=("Helvetica", 10, "bold"),
                             borderwidth=0,
                             focusthickness=3,
                             focuscolor='none',
                             padding=10)
        self.style.map("TButton", background=[('active', '#2980b9')])

        self.create_widgets()

    def create_widgets(self):
        title_label = tk.Label(self.first_frame, text="Welcome to Computer Science Chat",
                            font=("Helvetica", 18, "bold"), bg="#f0f0f0", fg="#333333")
        title_label.pack(pady=(20, 10))

        self.profile_label = tk.Label(self.first_frame, bg="#e0e0e0", width=15, height=7)
        self.profile_label.place(relx=0.5, y=150, anchor='center')

        upload_button = ttk.Button(self.first_frame, text="Upload Image", command=self.add_photo)
        upload_button.pack(pady=(120, 20)) 

        username_frame = tk.Frame(self.first_frame, bg="#f0f0f0")
        username_frame.pack(fill=tk.X, pady=10)

        username_label = tk.Label(username_frame, text="Username:",
                                font=("Helvetica", 10), bg="#f0f0f0", fg="#333333")
        username_label.pack(side=tk.LEFT, padx=(0, 10))

        self.username_entry = tk.Entry(username_frame, font=("Helvetica", 10),
                                    bg="white", fg="#333333", relief=tk.FLAT)
        self.username_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        connect_button = ttk.Button(self.first_frame, text="Connect", command=self.process_data)
        connect_button.pack(pady=20)

    def attach_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            if file_size > 10 * 1024 * 1024:  
                messagebox.showerror("Error", "File size exceeds 10MB limit.")
                return
            
            self.sent_message_format(None, f"Sending file: {file_name}")
            self.send_file(file_path, file_name)

    def send_file(self, file_path, file_name):
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            data = {
                'type': 'file',
                'from': self.user_id,
                'file_name': file_name,
                'file_data': file_data
            }
            data_bytes = pickle.dumps(data)
            
            size = len(data_bytes)
            self.client_socket.send('file'.encode())
            self.client_socket.send(struct.pack('!I', size))
            
            self.client_socket.send(data_bytes)
            
            print(f"File sent: {file_name}")
        except Exception as e:
            print(f"Error sending file: {e}")
            messagebox.showerror("Error", f"Failed to send file: {e}")

    def add_photo(self):
        self.image_path = filedialog.askopenfilename()
        if self.image_path:
            image_name = os.path.basename(self.image_path)
            self.image_extension = image_name[image_name.rfind('.')+1:]

            user_image = Image.open(self.image_path)
            user_image = user_image.resize((150, 150), Image.LANCZOS)
            self.profile_image = ImageTk.PhotoImage(user_image)

            self.profile_label.config(image=self.profile_image, width=150, height=150)
            self.profile_label.image = self.profile_image

    def process_data(self):
        if self.username_entry.get():
            self.profile_label.config(image="")

            if len((self.username_entry.get()).strip()) > 6:
                self.user = self.username_entry.get()[:6]+"."
            else:
                self.user = self.username_entry.get()

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect(("localhost", 9999))
                status = client_socket.recv(1024).decode()
                if status == 'not_allowed':
                    client_socket.close()
                    messagebox.showinfo(title="Can't connect!", message='Sorry, server is completely occupied. Try again later')
                    return
            except ConnectionRefusedError:
                messagebox.showinfo(title="Can't connect!", message="Server is offline, try again later.")
                print("Server is offline, try again later.")
                return

            client_socket.send(self.user.encode('utf-8'))

            if not self.image_path:
                self.image_path = self.user_image
            with open(self.image_path, 'rb') as image_data:
                image_bytes = image_data.read()

            image_len = len(image_bytes)
            image_len_bytes = struct.pack('i', image_len)
            client_socket.send(image_len_bytes)

            if client_socket.recv(1024).decode() == 'received':
                client_socket.send(str(self.image_extension).strip().encode())

            client_socket.send(image_bytes)

            clients_data_size_bytes = client_socket.recv(1024*8)
            clients_data_size_int = struct.unpack('i', clients_data_size_bytes)[0]
            b = b''
            while True:
                clients_data_bytes = client_socket.recv(1024)
                b += clients_data_bytes
                if len(b) == clients_data_size_int:
                    break

            clients_connected = pickle.loads(b)

            client_socket.send('image_received'.encode())

            user_id = struct.unpack('i', client_socket.recv(1024))[0]
            print(f"{self.user} is user no. {user_id}")
            try:
                chat_screen = ChatScreen(self, self.first_frame, client_socket, clients_connected, user_id)
                self.withdraw()
                chat_screen.grab_set()
            except Exception as e:
                print(f"Error creating ChatScreen: {e}")
                messagebox.showerror("Error", f"Failed to open chat screen: {e}")

class ChatScreen(tk.Toplevel):
    def __init__(self, parent, first_frame, client_socket, clients_connected, user_id):
        super().__init__(parent)

        self.window = 'ChatScreen'
        self.parent = parent
        self.first_frame = first_frame
        self.client_socket = client_socket
        self.clients_connected = clients_connected
        self.user_id = user_id
        self.all_user_image = {}
        self.entry_frame = None

        icon_path = os.path.join(os.path.dirname(__file__), 'images', 'chatapp_ca.ico')
        self.iconbitmap(icon_path)

        self.title("Computer Science Chat App")
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        x_co = int((screen_width / 2) - (680 / 2))
        y_co = int((screen_height / 2) - (750 / 2)) - 80
        self.geometry(f"680x750+{x_co}+{y_co}")

        self.configure(bg="#f0f0f0")
        self.bind('<Return>', lambda e: self.sent_message_format(e))

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        user_image = Image.open(self.parent.image_path)
        user_image = user_image.resize((40, 40), Image.LANCZOS)
        self.user_image = ImageTk.PhotoImage(user_image)

        global group_photo
        group_photo = Image.open('images/group_ca.png')
        group_photo = group_photo.resize((60, 60), Image.LANCZOS)
        group_photo = ImageTk.PhotoImage(group_photo)

        self.y = 180
        self.clients_online_labels = {}

        self.create_widgets()

        self.clients_online([])

        t = threading.Thread(target=self.receive_data)
        t.setDaemon(True)
        t.start()
    
    def attach_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            if file_size > 10 * 1024 * 1024:  
                messagebox.showerror("Error", "File size exceeds 10MB limit.")
                return
            
            self.sent_message_format(message=f"Sending file: {file_name}")
            
            self.send_file(file_path, file_name)

    def send_file(self, file_path, file_name):
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            data = {
                'type': 'file',
                'from': self.user_id,
                'file_name': file_name,
                'file_data': file_data
            }
            data_bytes = pickle.dumps(data)
            
            size = len(data_bytes)
            self.client_socket.send('file'.encode())
            self.client_socket.send(struct.pack('!I', size))
            
            self.client_socket.send(data_bytes)
            
            print(f"File sent: {file_name}")
        except Exception as e:
            print(f"Error sending file: {e}")
            messagebox.showerror("Error", f"Failed to send file: {e}")

    def create_widgets(self):
        header_frame = tk.Frame(self, bg="#3498db", padx=10, pady=10)
        header_frame.place(x=0, y=0, relwidth=1)

        group_label = tk.Label(header_frame, image=group_photo, bg="#3498db")
        group_label.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(header_frame, text="Group Chat", font=("Helvetica", 15, "bold"), fg="white",
                 bg="#3498db", anchor="w", justify="left").pack(side=tk.LEFT)

        tk.Label(self, text="Online", font=("Helvetica", 12, "bold"), fg="#40C961", bg="#f0f0f0").place(x=545, y=120)

        container = tk.Frame(self, bg="#f0f0f0")
        container.place(x=40, y=120, width=450, height=550)
        self.canvas = tk.Canvas(container, bg="#ffffff", highlightthickness=0)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#ffffff")

        scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def configure_scroll_region(e):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        def resize_frame(e):
            self.canvas.itemconfig(scrollable_window, width=e.width)

        self.scrollable_frame.bind("<Configure>", configure_scroll_region)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.yview_moveto(1.0)

        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", resize_frame)
        self.canvas.pack(fill="both", expand=True)

        self.entry_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        self.entry_frame.place(x=40, y=680, width=450)

        self.entry = tk.Text(self.entry_frame, font=("Helvetica", 10), width=25, height=2,
                            highlightcolor="#3498db", highlightthickness=1, relief="flat")
        self.entry.pack(side=tk.LEFT, padx=(0, 10), fill="both", expand=True)

        send_button = tk.Button(self.entry_frame, text="Send", fg="white", font=("Helvetica", 9, "bold"), bg="#3498db",
                                padx=5, pady=5, relief="flat", width=4, command=self.sent_message_format)
        send_button.pack(side=tk.RIGHT)

        self.entry.focus_set()

        self.add_emojis()

        attach_icon = Image.open('images/clip.png')
        attach_icon = attach_icon.resize((20, 20), Image.LANCZOS)
        self.attach_icon = ImageTk.PhotoImage(attach_icon)

        self.attach_button = tk.Button(self.entry_frame, image=self.attach_icon, bg="#f0f0f0",
                                    relief="flat", command=self.attach_file)
        self.attach_button.pack(side=tk.LEFT, padx=(5, 0))

    def add_emojis(self):
        emoji_data = [('emojis/u0001f44a.png', '\U0001F44A'), ('emojis/u0001f44c.png', '\U0001F44C'),
                      ('emojis/u0001f44d.png', '\U0001F44D'),
                      ('emojis/u0001f495.png', '\U0001F495'), ('emojis/u0001f496.png', '\U0001F496'),
                      ('emojis/u0001f4a6.png', '\U0001F4A6'),
                      ('emojis/u0001f4a9.png', '\U0001F4A9'), ('emojis/u0001f4af.png', '\U0001F4AF'),
                      ('emojis/u0001f595.png', '\U0001F595'),
                      ('emojis/u0001f600.png', '\U0001F600'), ('emojis/u0001f602.png', '\U0001F602'),
                      ('emojis/u0001f603.png', '\U0001F603'),
                      ('emojis/u0001f605.png', '\U0001F605'), ('emojis/u0001f606.png', '\U0001F606'),
                      ('emojis/u0001f608.png', '\U0001F608'),
                      ('emojis/u0001f60d.png', '\U0001F60D'), ('emojis/u0001f60e.png', '\U0001F60E'),
                      ('emojis/u0001f60f.png', '\U0001F60F'),
                      ('emojis/u0001f610.png', '\U0001F610'), ('emojis/u0001f618.png', '\U0001F618'),
                      ('emojis/u0001f61b.png', '\U0001F61B'),
                      ('emojis/u0001f61d.png', '\U0001F61D'), ('emojis/u0001f621.png', '\U0001F621'),
                      ('emojis/u0001f624.png', '\U0001F621'),
                      ('emojis/u0001f631.png', '\U0001F631'), ('emojis/u0001f632.png', '\U0001F632'),
                      ('emojis/u0001f634.png', '\U0001F634'),
                      ('emojis/u0001f637.png', '\U0001F637'), ('emojis/u0001f642.png', '\U0001F642'),
                      ('emojis/u0001f64f.png', '\U0001F64F'),
                      ('emojis/u0001f920.png', '\U0001F920'), ('emojis/u0001f923.png', '\U0001F923'),
                      ('emojis/u0001f928.png', '\U0001F928')]

        emoji_x_pos = 490
        emoji_y_pos = 520
        for Emoji in emoji_data:
            emojis = Image.open(Emoji[0])
            emojis = emojis.resize((20, 20), Image.LANCZOS)
            emojis = ImageTk.PhotoImage(emojis)

            emoji_unicode = Emoji[1]
            emoji_label = tk.Label(self, image=emojis, text=emoji_unicode, bg="#f0f0f0", cursor="hand2")
            emoji_label.image = emojis
            emoji_label.place(x=emoji_x_pos, y=emoji_y_pos)
            emoji_label.bind('<Button-1>', lambda x: self.insert_emoji(x))

            emoji_x_pos += 25
            cur_index = emoji_data.index(Emoji)
            if (cur_index + 1) % 6 == 0:
                emoji_y_pos += 25
                emoji_x_pos = 490

    def receive_data(self):
        while True:
            try:
                data_type = self.client_socket.recv(1024).decode()

                if data_type == 'file':
                    size_data = self.client_socket.recv(4)
                    size = struct.unpack('!I', size_data)[0]
                    
                    file_data = b''
                    while len(file_data) < size:
                        chunk = self.client_socket.recv(min(1024, size - len(file_data)))
                        if not chunk:
                            raise ConnectionError("Connection closed while receiving file")
                        file_data += chunk
                    
                    file_info = pickle.loads(file_data)
                    self.handle_received_file(file_info)

                elif data_type == 'notification':
                    data_size = b''
                    while len(data_size) < 4:
                        chunk = self.client_socket.recv(4 - len(data_size))
                        if not chunk:
                            raise ConnectionResetError("Connection closed while receiving data size")
                        data_size += chunk
                    
                    data_size_int = struct.unpack('i', data_size)[0]

                    b = b''
                    while len(b) < data_size_int:
                        chunk = self.client_socket.recv(min(1024, data_size_int - len(b)))
                        if not chunk:
                            raise ConnectionResetError("Connection closed while receiving data")
                        b += chunk
                    
                    data = pickle.loads(b)
                    self.notification_format(data)

                else:
                    data_bytes = self.client_socket.recv(1024)
                    data = pickle.loads(data_bytes)
                    self.received_message_format(data)

            except ConnectionAbortedError:
                print("You disconnected...")
                self.client_socket.close()
                break
            except ConnectionResetError as e:
                print(f"Connection error: {e}")
                messagebox.showinfo(title='No Connection!', message="Server offline... try connecting again later")
                self.client_socket.close()
                self.first_screen()
                break
            except struct.error as e:
                print(f"Data structure error: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error: {e}")
                continue

    def on_closing(self):
        if messagebox.askyesno(title='Warning!', message="Do you really want to disconnect?"):
            try:
                import os
                os.remove(self.all_user_image[self.user_id])
            except Exception as e:
                print(f"Error removing image: {e}")
            self.client_socket.close()
            self.destroy()
            self.parent.deiconify()

    def handle_received_file(self, file_info):
        file_name = file_info['file_name']
        file_data = file_info['file_data']
        from_ = file_info['from']
        
        save_path = filedialog.asksaveasfilename(defaultextension=".*",
                                                initialfile=file_name,
                                                title="Save received file")
        if save_path:
            with open(save_path, 'wb') as file:
                file.write(file_data)
            
            print(f"File received and saved: {save_path}")
        else:
            print("File save cancelled by user")

    def received_message_format(self, data):
        message = data['message']
        from_ = data['from']

        sender_image = self.clients_connected[from_][1]
        sender_image_extension = self.clients_connected[from_][2]

        with open(f"{from_}.{sender_image_extension}", 'wb') as f:
            f.write(sender_image)

        im = Image.open(f"{from_}.{sender_image_extension}")
        im = im.resize((40, 40), Image.LANCZOS)
        im = ImageTk.PhotoImage(im)

        m_frame = tk.Frame(self.scrollable_frame, bg="#ffffff")

        m_frame.columnconfigure(1, weight=1)

        t_label = tk.Label(m_frame, bg="#ffffff", fg="#333333", text=datetime.now().strftime('%H:%M'),
                           font=("Helvetica", 7, "bold"), justify="left", anchor="w")
        t_label.grid(row=0, column=1, padx=2, sticky="w")

        m_label = tk.Label(m_frame, wraplength=250, fg="#333333", bg="#e1e1e1", text=message,
                           font=("Helvetica", 9), justify="left", anchor="w", padx=5, pady=5)
        m_label.grid(row=1, column=1, padx=2, pady=2, sticky="w")

        i_label = tk.Label(m_frame, bg="#ffffff", image=im)
        i_label.image = im
        i_label.grid(row=0, column=0, rowspan=2)

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def sent_message_format(self, event=None, message=None):
        if message is None:
            message = self.entry.get('1.0', 'end-1c')

        if message:
            if event:
                message = message.strip()
            self.entry.delete("1.0", "end-1c")

            from_ = self.user_id

            data = {'from': from_, 'message': message}
            data_bytes = pickle.dumps(data)

            self.client_socket.send('message'.encode())
            self.client_socket.send(data_bytes)

            m_frame = tk.Frame(self.scrollable_frame, bg="#ffffff")

            m_frame.columnconfigure(0, weight=1)

            t_label = tk.Label(m_frame, bg="#ffffff", fg="#333333", text=datetime.now().strftime('%H:%M'),
                            font=("Helvetica", 7, "bold"), justify="right", anchor="e")
            t_label.grid(row=0, column=0, padx=2, sticky="e")

            m_label = tk.Label(m_frame, wraplength=250, text=message, fg="#333333", bg="#3498db",
                            font=("Helvetica", 9), justify="left", anchor="e", padx=5, pady=5)
            m_label.grid(row=1, column=0, padx=2, pady=2, sticky="e")

            i_label = tk.Label(m_frame, bg="#ffffff", image=self.user_image)
            i_label.image = self.user_image
            i_label.grid(row=0, column=1, rowspan=2, sticky="e")

            m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

            self.canvas.update_idletasks()
            self.canvas.yview_moveto(1.0)

    def notification_format(self, data):
        if data['n_type'] == 'joined':
            name = data['name']
            image = data['image_bytes']
            extension = data['extension']
            message = data['message']
            client_id = data['id']
            self.clients_connected[client_id] = (name, image, extension)
            self.clients_online([client_id, name, image, extension])

        elif data['n_type'] == 'left':
            client_id = data['id']
            message = data['message']
            self.remove_labels(client_id)
            del self.clients_connected[client_id]

        m_frame = tk.Frame(self.scrollable_frame, bg="#ffffff")

        t_label = tk.Label(m_frame, fg="#333333", bg="#ffffff", text=datetime.now().strftime('%H:%M'),
                           font=("Helvetica", 7, "bold"))
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=message, font=("Helvetica", 9, "bold"),
                           justify="left", bg="#d4edda", fg="#155724", padx=5, pady=5)
        m_label.pack()

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.yview_moveto(1.0)

    def clients_online(self, new_added):
        if not new_added:
            for user_id in self.clients_connected:
                name = self.clients_connected[user_id][0]
                image_bytes = self.clients_connected[user_id][1]
                extension = self.clients_connected[user_id][2]

                with open(f"{user_id}.{extension}", 'wb') as f:
                    f.write(image_bytes)

                self.all_user_image[user_id] = f"{user_id}.{extension}"

                user = Image.open(f"{user_id}.{extension}")
                user = user.resize((45, 45), Image.LANCZOS)
                user = ImageTk.PhotoImage(user)

                display_name = f"{name} (me)" if user_id == self.user_id else name

                b = tk.Label(self, image=user, text=display_name, compound="left", fg="#333333", bg="#f0f0f0",
                            font=("Helvetica", 10), padx=5, pady=5)
                b.image = user
                self.clients_online_labels[user_id] = (b, self.y)

                b.place(x=500, y=self.y)
                self.y += 60

        else:
            user_id = new_added[0]
            name = new_added[1]
            image_bytes = new_added[2]
            extension = new_added[3]

            with open(f"{user_id}.{extension}", 'wb') as f:
                f.write(image_bytes)

            self.all_user_image[user_id] = f"{user_id}.{extension}"

            user = Image.open(f"{user_id}.{extension}")
            user = user.resize((45, 45), Image.LANCZOS)
            user = ImageTk.PhotoImage(user)

            b = tk.Label(self, image=user, text=name, compound="left", fg="#333333", bg="#f0f0f0",
                         font=("Helvetica", 10), padx=5, pady=5)
            b.image = user
            self.clients_online_labels[user_id] = (b, self.y)

            b.place(x=500, y=self.y)
            self.y += 60

    def remove_labels(self, client_id):
        for user_id in self.clients_online_labels.copy():
            b = self.clients_online_labels[user_id][0]
            y_co = self.clients_online_labels[user_id][1]
            if user_id == client_id:
                print("yes")
                b.destroy()
                del self.clients_online_labels[client_id]
                import os
                os.remove(self.all_user_image[user_id])

            elif user_id > client_id:
                y_co -= 60
                b.place(x=500, y=y_co)
                self.clients_online_labels[user_id] = (b, y_co)
                self.y -= 60

    def insert_emoji(self, x):
        self.entry.insert("end-1c", x.widget['text'])

    def first_screen(self):
        self.destroy()
        self.parent.geometry(f"550x400+{self.parent.x_co}+{self.parent.y_co}")
        self.parent.first_frame.pack(fill="both", expand=True)
        self.window = None

if __name__ == "__main__":
    icon_path = os.path.join(os.path.dirname(__file__), 'images', 'chatapp_ca.ico')
    app = FirstScreen()
    app.iconbitmap(icon_path)
    app.mainloop()