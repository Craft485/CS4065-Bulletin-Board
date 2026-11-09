import socket, threading, argparse


from datetime import datetime
from protocol import build_packet, read_packet

users = {}
messages = []
next_message_id = 1
lock = threading.Lock()


def send_packet(client_socket, command, *fields):
  try:
    client_socket.sendall(build_packet(command, *fields).encode())
  except OSError:
    pass


def broadcast(command, *fields, exclude=None):
  with lock:
    clients = [client for client in users.values() if client is not exclude]
  for client in clients:
    send_packet(client, command, *fields)

def handle_client_connection(client_socket: socket.socket):
  print(f"Handling client connection for {client_socket.getsockname()}")


  # Create a file-like object for reading from the socket
  reader = client_socket.makefile("r")
  username = None

  # Handle incoming packets from the client
  try:
    while True:
      packet = read_packet(reader) # keep reading packets from the client until the connection is closed or an error occurs
      if packet is None:
        break

      #a packet is a tuple of (command, fields) where command is a string and fields is a list of strings
      command, fields = packet 

      # if the command is JOIN and the username is not already taken, add the user to the users 
      # dictionary and send them the list of users and recent messages
      if command == "JOIN" and fields: 
        username = fields[0]


        # this is to ensure that the users dictionary is not modified by another thread 
        # while we are checking if the username is already taken
        with lock: 
          if username in users:
            username = None
            send_packet(client_socket, "ERROR", "Name already in use")
            continue
          users[username] = client_socket
          user_list = list(users)

          #display the last two messages to the user who just joined
          recent_messages = messages[-2:]

      # send the user the list of users and recent messages, and broadcast to all other users
      #  that a new user has joined
        send_packet(client_socket, "USER_LIST", *user_list)
        for message in recent_messages:
          send_packet(client_socket, "MESSAGE_SUMMARY", *message[:4])
        broadcast("USER_JOINED", username, exclude=client_socket)

      # if the command is POST and the user has joined, add the message to the messages
      # list and broadcast it to all users
      elif command == "POST" and username and len(fields) >= 2:
        global next_message_id
        message = [
          str(next_message_id), username,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          fields[0], "\n".join(fields[1:])
        ]
        with lock:
          next_message_id += 1
          messages.append(message)
        broadcast("POST", *message)

      elif command == "USERS":
        with lock:
          send_packet(client_socket, "USER_LIST", *users.keys())

      # if the command is MESSAGE and the user has joined (or online), 
      # send the message content to the user
      elif command == "MESSAGE" and fields:
        with lock:
          message = next((item for item in messages if item[0] == fields[0]), None)
        if message:
          send_packet(client_socket, "MESSAGE_CONTENT", *message)
        else:
          send_packet(client_socket, "ERROR", "Message not found")


      # if the command is LEAVE, send a GOODBYE packet to the client and 
      # break the loop to close the connection
      elif command == "LEAVE":
        send_packet(client_socket, "GOODBYE")
        break
      else:
        send_packet(client_socket, "ERROR", "Invalid command or arguments")
  finally:
    if username:
      with lock:
        users.pop(username, None)
      broadcast("USER_LEFT", username)
    reader.close()
    client_socket.close()

def main():
  # Grab optional command line argument for the port for the server to listen on
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument("--port", type=int, default=3001)
  args = arg_parser.parse_args()
  
  # Create and setup server's socket
  # Initalize an IPv4 (AF_INET) socket that uses TCP ordered byte streams (SOCK_STREAM)
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # Enable the SO_REUSEADDR option on the socket, this is mostly a formality to alter the behavior of bind
  # the new behavior enables easier recovery if the server were to be closed and quickly restarted
  server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  # Set a timeout of 1 second to allow for keyboard interrupts
  server_socket.settimeout(1.0)
  
  # Have the server listen for connections
  server_socket.bind(("127.0.0.1", args.port))
  server_socket.listen()
  print(f"Server listening on port {args.port}")
  
  # Accept new client connections
  # While leaving a window of time open for keyboard interrupts telling the server to close
  try:
    while True:
      try:
        client_socket, client_address = server_socket.accept()
      except socket.timeout:
        # No new connections yet, retry
        continue
      print(f"Connection created: {client_address}")
      # Handle client connection on a new thread
      threading.Thread(target=handle_client_connection, args=(client_socket,), daemon=True).start()
  except KeyboardInterrupt:
    print("Closing server...")
  finally:
    server_socket.close()

if __name__ == "__main__":
  main()
