import queue
import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from protocol import build_packet, read_packet


class BulletinBoardGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulletin Board Test Client")
        self.root.geometry("700x500")

        self.sock = None
        self.reader = None
        self.generation = 0
        self.join_pending = False
        self.joined = False
        self.username = ""
        self.events = queue.Queue()
        self.users = []
        self.messages = {}

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._process_events)

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.connection_tab = ttk.Frame(self.notebook, padding=12)
        self.post_tab = ttk.Frame(self.notebook, padding=12)
        self.users_tab = ttk.Frame(self.notebook, padding=12)
        self.messages_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.connection_tab, text="Connect / Join")
        self.notebook.add(self.post_tab, text="Post")
        self.notebook.add(self.users_tab, text="Users")
        self.notebook.add(self.messages_tab, text="Messages")

        self.address_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="3001")
        self.username_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Disconnected")

        ttk.Label(self.connection_tab, text="Server address").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(self.connection_tab, textvariable=self.address_var, width=30).grid(
            row=0, column=1, sticky="ew", pady=4
        )
        ttk.Label(self.connection_tab, text="Port").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(self.connection_tab, textvariable=self.port_var, width=12).grid(
            row=1, column=1, sticky="w", pady=4
        )
        ttk.Button(self.connection_tab, text="Connect", command=self.connect).grid(
            row=2, column=1, sticky="w", pady=6
        )
        ttk.Label(self.connection_tab, text="Username").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(self.connection_tab, textvariable=self.username_var, width=30).grid(
            row=3, column=1, sticky="ew", pady=4
        )
        ttk.Button(self.connection_tab, text="Join public board", command=self.join).grid(
            row=4, column=1, sticky="w", pady=6
        )
        ttk.Button(self.connection_tab, text="Leave / disconnect", command=self.leave).grid(
            row=5, column=1, sticky="w", pady=4
        )
        ttk.Label(self.connection_tab, textvariable=self.status_var).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(12, 4)
        )
        ttk.Label(self.connection_tab, text="Activity").grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(12, 4)
        )
        self.activity = tk.Listbox(self.connection_tab, height=10)
        self.activity.grid(row=8, column=0, columnspan=2, sticky="nsew")
        self.connection_tab.columnconfigure(1, weight=1)
        self.connection_tab.rowconfigure(8, weight=1)

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

        ttk.Button(self.users_tab, text="Refresh users", command=self.request_users).pack(anchor="w")
        self.user_list = tk.Listbox(self.users_tab)
        self.user_list.pack(fill="both", expand=True, pady=(8, 0))

        ttk.Label(
            self.messages_tab,
            text="Recent messages and new posts (select one to fill its ID below)",
        ).pack(anchor="w")
        self.message_list = tk.Listbox(self.messages_tab, height=10)
        self.message_list.pack(fill="both", expand=True, pady=(6, 8))
        self.message_list.bind("<<ListboxSelect>>", self._select_message)
        lookup_row = ttk.Frame(self.messages_tab)
        lookup_row.pack(fill="x")
        ttk.Label(lookup_row, text="Message ID").pack(side="left")
        self.message_id_var = tk.StringVar()
        ttk.Entry(lookup_row, textvariable=self.message_id_var, width=12).pack(
            side="left", padx=6
        )
        ttk.Button(lookup_row, text="Get full message", command=self.get_message).pack(side="left")
        self.message_content = tk.Text(self.messages_tab, height=6, wrap="word", state="disabled")
        self.message_content.pack(fill="x", pady=(8, 0))

    def _log(self, text):
        self.activity.insert("end", text)
        self.activity.see("end")

    def connect(self):
        if self.sock is not None:
            messagebox.showinfo("Already connected", "Disconnect before connecting again.")
            return

        try:
            port = int(self.port_var.get())
            sock = socket.create_connection((self.address_var.get().strip(), port), timeout=5)
            sock.settimeout(None)
            reader = sock.makefile("r")
        except (OSError, ValueError) as error:
            messagebox.showerror("Connection failed", str(error))
            return

        self.generation += 1
        generation = self.generation
        self.sock = sock
        self.reader = reader
        self.join_pending = False
        self.joined = False
        self.status_var.set(f"Connected to {self.address_var.get()}:{port}")
        self._log(f"Connected to {self.address_var.get()}:{port}")
        threading.Thread(
            target=self._receive_packets, args=(sock, reader, generation), daemon=True
        ).start()

    def _receive_packets(self, sock, reader, generation):
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

    def _send(self, command, *fields):
        if self.sock is None:
            messagebox.showwarning("Not connected", "Connect to a server first.")
            return False
        try:
            self.sock.sendall(build_packet(command, *fields).encode())
            return True
        except OSError as error:
            self._log(f"Send failed: {error}")
            self._disconnect()
            return False

    def join(self):
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning("Username required", "Enter a username before joining.")
            return
        if self.joined or self.join_pending:
            return
        if self._send("JOIN", username):
            self.username = username
            self.join_pending = True
            self.status_var.set(f"Joining as {username}...")

    def leave(self):
        if self.sock is None:
            return
        if self.joined:
            self._send("LEAVE")
            self.status_var.set("Leaving the board...")
        else:
            self._disconnect()

    def post(self):
        subject = self.subject_entry.get().strip()
        content = self.content_entry.get().strip()
        if not subject or not content:
            messagebox.showwarning("Missing message", "Enter both a subject and message.")
            return
        if self.joined and self._send("POST", subject, content):
            self.content_entry.delete(0, "end")
            self._log("Post sent.")
        elif not self.joined:
            messagebox.showwarning("Not joined", "Join the board before posting.")

    def request_users(self):
        if not self.joined:
            messagebox.showwarning("Not joined", "Join the board before requesting users.")
            return
        self._send("USERS")

    def get_message(self):
        message_id = self.message_id_var.get().strip()
        if not message_id:
            messagebox.showwarning("Message ID required", "Enter a message ID.")
            return
        if not self.joined:
            messagebox.showwarning("Not joined", "Join the board before requesting messages.")
            return
        self._send("MESSAGE", message_id)

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
                self._log(f"Connection error: {data}")
            elif event_type == "closed":
                self._disconnect()
        self.root.after(100, self._process_events)

    def _handle_packet(self, command, fields):
        if command == "USER_LIST":
            self.users = fields
            self._refresh_users()
            if self.join_pending:
                self.join_pending = False
                self.joined = True
                self.status_var.set(f"Joined as {self.username}")
                self._log(f"Joined the board as {self.username}.")
        elif command in ("MESSAGE_SUMMARY", "POST"):
            self._add_message(fields)
            if command == "POST" and len(fields) >= 5:
                self._log(f"New post from {fields[1]}: {fields[3]}")
        elif command == "MESSAGE_CONTENT":
            if len(fields) >= 5:
                details = (
                    f"ID: {fields[0]}\nSender: {fields[1]}\n"
                    f"Date: {fields[2]}\nSubject: {fields[3]}\n\n{fields[4]}"
                )
                self.message_content.configure(state="normal")
                self.message_content.delete("1.0", "end")
                self.message_content.insert("1.0", details)
                self.message_content.configure(state="disabled")
        elif command in ("USER_JOINED", "USER_LEFT"):
            if fields:
                action = "joined" if command == "USER_JOINED" else "left"
                self._log(f"{fields[0]} {action} the board.")
        elif command == "ERROR":
            self.join_pending = False
            self._log("Server error: " + " | ".join(fields))
            if not self.joined:
                self.status_var.set("Connected; join was not completed.")
        elif command == "GOODBYE":
            self._log("Server confirmed that you left.")
            self._disconnect()
        else:
            self._log(f"[{command}] {' | '.join(fields)}")

    def _add_message(self, fields):
        if len(fields) < 4:
            return
        message_id, sender, posted_at, subject = fields[:4]
        self.messages[message_id] = (sender, posted_at, subject)
        self.message_list.delete(0, "end")
        for current_id, (current_sender, current_date, current_subject) in self.messages.items():
            self.message_list.insert(
                "end", f"{current_id}, {current_sender}, {current_date}, {current_subject}"
            )

    def _select_message(self, _event):
        selection = self.message_list.curselection()
        if selection:
            item = self.message_list.get(selection[0])
            self.message_id_var.set(item.split(",", 1)[0])

    def _refresh_users(self):
        self.user_list.delete(0, "end")
        for username in self.users:
            self.user_list.insert("end", username)

    def _disconnect(self):
        sock = self.sock
        self.sock = None
        self.reader = None
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
        self.status_var.set("Disconnected")

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
