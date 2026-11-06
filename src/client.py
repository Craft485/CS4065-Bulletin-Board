import threading, socket
from protocol import build_packet, read_packet

class Client:
    def __init__(self):
        # This is the connected socket, None means disconnected.
        self.sock = None

        # The line reader wrapped around the socket.
        self.sock_reader = None

    def connect(self, address, port):
        """
        Open a TCP connection and start the receiver thread.

        Args:
            address (str): The hostname or IP address.
            port (str): The port.
        """
        # Avoid multiple connections, if self.sock is not None, there is a connection.        
        if self.sock:
            print("Already connected.")
            return

        try:
            # Initialize and connect the socket using the address and port number.
            self.sock = socket.create_connection((address, int(port)))
        except (OSError, ValueError) as e:
            # OSError for connection/server issues and ValueError if the port was not a number.
            print(f"Could not connect: {e}")
            return

        # Set up the reader from the connected socket.
        print(f"Connected to {address}:{port}")
        self.sock_reader = self.sock.makefile("r")

        # TODO: Create thread for receiving packets
        # Client has to wait for user input or reading a packet, both of these 
        # can block the other so this additional thread allows both.
        # "Display incoming notifications and posts from other users as they arrive"

    def close(self):
        """
        Close the socket.
        """
        if self.sock:
            self.sock.close()
        self.sock = None
        self.sock_reader = None

    def send(self, command: str, *fields: str):
        """
        Sends a packet to the server: the command, each field (fields separated by a newline), 
        and ended with two newlines.

        Args:
            command (str): The first line of the packet, like "POST".
            *fields (str): Zero or more strings for however many fields the command needs.
        """
        # Not connected warning if user tries to run commands being connected.
        if not self.sock:
            print("Not connected. Use '%connect <address> <port>' before running commands")
            return

        try:
            # Encodes the text to bytes and sends all of them.
            self.sock.sendall(build_packet(command, *fields).encode())
        except OSError:
            # Failure to send means the connection is no longer there.
            print(f"Connection failed.")
            self.close()

    def cmd_connect(self, args: str):
        """
        %connect <address> <port>

        Args:
            args (str): String representing the command fields provided by the user.
        """
        # There should only be two arguments (address and port), display a usage message if there are not.
        parts = args.split()
        if len(parts) != 2:
            print(f"Usage: %connect <address> <port>")
            return

        address, port = parts
        self.connect(address, port)

    def run(self):
        """
        Read commands until the user exits.
        """
        print("Bulletin Board Client")
        print("Run: %connect <address> <port> to begin.")

        while True:
            user_input = input().strip()

            # Ignore empty user input.
            if not user_input:
                continue

            # Separate the token before the first space into command (will be something like %post),
            # everything after the space are the command fields.
            command, _, args = user_input.partition(" ")
            args = args.strip()

            if command == "%connect":
                self.cmd_connect(args)
            elif command == "%join":
                pass
            elif command == "%post":
                pass
            elif command == "%message":
                pass
            elif command == "%users":
                pass
            elif command == "%leave":
                pass
            elif command == "%exit":
                # Exit the loop, socket will then close.
                break
            else:
                print(f"Unkown command {command}")

        # Close socket
        self.close()

if __name__ == "__main__":
    Client().run()