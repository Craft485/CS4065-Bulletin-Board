import queue
import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from protocol import build_packet, read_packet


class BulletinBoardGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulletin Board")
        self.root.geometry("700x520")


        #initialize empty and placeholder variables
        self.sock = None
        self.generation = 0
        self.join_pending = False
        self.joined = False
        self.username = ""
        self.events = queue.Queue()
        self.users = []
        self.messages = {}
        self.message_order = []

        #build the user interface and set up event handling 
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close) #if the command is closed, call the _on_close method to clean up resources
        self.root.after(100, self._process_events)
        self.username_entry.focus_set() # set the focus to the username entry field when the application just open up

    def _build_ui(self):
        self.login_frame = ttk.Frame(self.root, padding=24)
        self.login_frame.pack(fill="both", expand=True)
        ttk.Label(
            self.login_frame, text="Welcome to the Bulletin Board", font=("", 16, "bold")
        ).pack(pady=(50, 12))
        ttk.Label(self.login_frame, text="Enter a unique username to join:").pack(pady=4)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(self.login_frame, textvariable=self.username_var, width=32)
        self.username_entry.pack(pady=6)
        self.username_entry.bind("<Return>", lambda _event: self.join())
        self.join_button = ttk.Button(self.login_frame, text="Join", command=self.join)
        self.join_button.pack(pady=8)
        self.login_status_var = tk.StringVar(value="Make sure the server is running on port 3001.")
        ttk.Label(self.login_frame, textvariable=self.login_status_var).pack(pady=6)

        self.main_frame = ttk.Frame(self.root, padding=10)
        header = ttk.Frame(self.main_frame)
        header.pack(fill="x", pady=(0, 8))
        self.status_var = tk.StringVar(value="")
        ttk.Label(header, textvariable=self.status_var).pack(side="left", fill="x", expand=True)
        ttk.Button(header, text="Leave board", command=self.leave).pack(side="right")

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True)
        self.users_tab = ttk.Frame(self.notebook, padding=12)
        self.messages_tab = ttk.Frame(self.notebook, padding=12)
        self.post_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.users_tab, text="Online Users")
        self.notebook.add(self.messages_tab, text="Messages Dashboard")
        self.notebook.add(self.post_tab, text="New Post")

        ttk.Button(self.users_tab, text="Refresh users", command=self.request_users).pack(
            anchor="w"
        )
        self.user_list = tk.Listbox(self.users_tab)
        self.user_list.pack(fill="both", expand=True, pady=(8, 0))

        ttk.Label(self.messages_tab, text="Select a post to view its full message:").pack(
            anchor="w"
        )
        self.message_list = tk.Listbox(self.messages_tab, height=10)
        self.message_list.pack(fill="both", expand=True, pady=(6, 8))
        self.message_list.bind("<<ListboxSelect>>", self._select_message)
        self.message_content = tk.Text(
            self.messages_tab, height=8, wrap="word", state="disabled"
        )
        self.message_content.pack(fill="x")

        ttk.Label(self.post_tab, text="Subject").grid(row=0, column=0, sticky="w", pady=4)
        self.subject_entry = ttk.Entry(self.post_tab)
        self.subject_entry.grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(self.post_tab, text="Message").grid(row=1, column=0, sticky="w", pady=4)
        self.content_entry = ttk.Entry(self.post_tab)
        self.content_entry.grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Button(self.post_tab, text="Post message", command=self.post).grid(
            row=2, column=1, sticky="w", pady=8
        )
        self.post_tab.columnconfigure(1, weight=1)

    def join(self): 
        # join method is called when the user clicks the "Join" button or presses Enter
        # in the username entry field. It retrieves the username from the entry field,
        # checks if it's valid, and attempts to connect to the server. If successful,
        #  it sends a JOIN command to the server with the username. If any step fails, it
        #  updates the login status with an appropriate message.


        username = self.username_var.get().strip()
        if not username:
            self.login_status_var.set("Please enter a username.")
            return
        if self.join_pending or self.joined:
            return

        if self.sock is None and not self._connect():
            return
        self.username = username
        self.join_pending = True
        self.join_button.configure(state="disabled")
        self.login_status_var.set(f"Joining as {username}...")
        if not self._send("JOIN", username):
            self.join_pending = False
            self.join_button.configure(state="normal")

    def _connect(self):
        #connect method attempts to establish a connection to the server, if it is not
        #online, display error message and return False.   
        try: 
            sock = socket.create_connection(("127.0.0.1", 3001), timeout=5)
            sock.settimeout(None)
            reader = sock.makefile("r")
        except OSError as error:
            self.login_status_var.set(f"Could not connect to the server: {error}")
            return False


        # If the connection is successful, it increments the generation counter, stores the socket,
        self.generation += 1
        generation = self.generation
        self.sock = sock
        threading.Thread(
            target=self._receive_packets, args=(reader, generation), daemon=True
        ).start()
        return True


    #receive_packets method runs in a separate thread and continuously reads packets from the server.
    def _receive_packets(self, reader, generation):
        try:
            while True:
                packet = read_packet(reader)
                if packet is None:
                    break
                self.events.put((generation, "packet", packet))
        except (OSError, UnicodeError) as error:
            self.events.put((generation, "error", str(error)))
        finally:
            try:
                reader.close()
            except OSError:
                pass
            self.events.put((generation, "closed", None))


    #send method sends a packet to the server with the specified command and fields. If the socket is None, it returns False. 
    # If sending fails due to an OSError, it shows an error message, disconnects, 
    # and returns to the login screen.


    def _send(self, command, *fields):
        if self.sock is None:
            return False
        try:
            self.sock.sendall(build_packet(command, *fields).encode())
            return True
        except OSError as error:
            self._show_message(f"Connection failed: {error}")
            self._disconnect()
            self._return_to_login()
            return False

    def leave(self):
        if self.joined:
            self.status_var.set("Leaving the board...")
            self._send("LEAVE")

    def post(self):
        subject = self.subject_entry.get().strip()
        content = self.content_entry.get().strip()
        if not subject or not content:
            #display a warning message if either the subject or content is missing
            messagebox.showwarning("Missing message", "Enter both a subject and message.")
            return
        if self._send("POST", subject, content):
            self.content_entry.delete(0, "end")

    def request_users(self):
        self._send("USERS")

    def _process_events(self):
        while True:
            try:
                generation, event_type, data = self.events.get_nowait()
            except queue.Empty:
                break
            if generation != self.generation:
                continue
            if event_type == "packet":
                self._handle_packet(*data)
            elif event_type == "error":
                self._show_message(f"Connection error: {data}")
            elif event_type == "closed":
                self._disconnect()
                self._return_to_login("Disconnected from the server. Enter a username to rejoin.")
        self.root.after(100, self._process_events)

    def _handle_packet(self, command, fields):
        if command == "USER_LIST":
            self.users = fields
            self._refresh_users()
            if self.join_pending:
                self.join_pending = False
                self.joined = True
                self.login_frame.pack_forget()
                self.main_frame.pack(fill="both", expand=True)
                self.status_var.set(f"Online as {self.username}")
        elif command in ("MESSAGE_SUMMARY", "POST"):
            self._add_message(fields)
        elif command == "MESSAGE_CONTENT":
            if len(fields) >= 5:
                details = (
                    f"ID: {fields[0]}\nSender: {fields[1]}\n"
                    f"Date: {fields[2]}\nSubject: {fields[3]}\n\n{fields[4]}"
                )
                self._set_message_content(details)
        elif command == "USER_JOINED" and fields:
            if fields[0] not in self.users:
                self.users.append(fields[0])
                self._refresh_users()
        elif command == "USER_LEFT" and fields:
            if fields[0] in self.users:
                self.users.remove(fields[0])
                self._refresh_users()
        elif command == "ERROR":
            error = "Server error: " + " | ".join(fields)
            if self.join_pending:
                self.join_pending = False
                self.join_button.configure(state="normal")
                self.login_status_var.set(error)
            else:
                self._show_message(error)
        elif command == "GOODBYE":
            self._disconnect()
            self._return_to_login("You left the board. Enter a username to rejoin.")


    # adds a new message to the messages dictionary (message_id: (sender, posted_at, subject))
    # and updates the message_order list to maintain the order of messages.

    def _add_message(self, fields):
        if len(fields) < 4:
            return
        message_id, sender, posted_at, subject = fields[:4]
        if message_id not in self.messages:
            self.message_order.append(message_id)
        self.messages[message_id] = (sender, posted_at, subject)
        selected_id = self._selected_message_id()
        self.message_list.delete(0, "end")
        for current_id in self.message_order:
            current_sender, current_date, current_subject = self.messages[current_id]
            self.message_list.insert(
                "end", f"{current_id}, {current_sender}, {current_date}, {current_subject}"
            )
        if selected_id in self.message_order:
            self.message_list.selection_set(self.message_order.index(selected_id))


    # if click on a message in the list, it retrieves the selected message ID and
    #  sends a MESSAGE command to the server to request the full content of that message.
    def _selected_message_id(self):
        selection = self.message_list.curselection()
        if selection and selection[0] < len(self.message_order):
            return self.message_order[selection[0]]
        return None

    def _select_message(self, _event):
        message_id = self._selected_message_id()
        if message_id:
            self._set_message_content("Loading message...")
            self._send("MESSAGE", message_id)

    def _set_message_content(self, text):
        self.message_content.configure(state="normal")
        self.message_content.delete("1.0", "end")
        self.message_content.insert("1.0", text)
        self.message_content.configure(state="disabled")

    def _refresh_users(self):
        self.user_list.delete(0, "end")
        for username in self.users:
            self.user_list.insert("end", username)

    def _show_message(self, text):
        if self.joined:
            self.status_var.set(text)
        else:
            self.login_status_var.set(text)

    def _disconnect(self):
        sock = self.sock
        self.sock = None
        self.join_pending = False
        self.joined = False
        self.username = ""
        self.generation += 1
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

    def _return_to_login(self, message=None):
        self.main_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)
        self.join_button.configure(state="normal")
        self.username_var.set("")
        if message:
            self.login_status_var.set(message)
        self.username_entry.focus_set()

    def _on_close(self):
        if self.sock is not None and self.joined:
            try:
                self.sock.sendall(build_packet("LEAVE").encode())
            except OSError:
                pass
        self._disconnect()
        self.root.destroy()


def main():
    root = tk.Tk()
    BulletinBoardGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
