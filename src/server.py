import socket, threading, argparse

# TODO: Implement client-to-server communication
def handle_client_connection(client_socket: socket.socket):
  print(f"Handling client connection for {client_socket.getsockname()}")

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
