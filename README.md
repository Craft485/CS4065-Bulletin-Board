# CS4065 Programming Assignment 2: Bulletin Board

Group members: Colin Davis, Huy Le, Caden Burks-D'amico

## Protocol:

Messages exchanged between the client and server will use a plaintext format.

Each "packet" will begin with the command the client wants to send. From this, the server will expect the remainder of the packet to include the fields that relate to that particular command.

Different fields within a packet will be separated with a single newline character.

The end of a packet will be represented with two subsequent newline characters.

## Running the server and test client

The project requires Python 3. No third-party packages are needed; the GUI uses
Python's standard-library Tkinter module.

Open two terminals from the project directory. In the first terminal, start the
server:

```text
cd src
python server.py
```

In the second terminal, start the standalone four-tab test client:

```text
cd src
python gui_client.py
```

In the **Connect / Join** tab, connect to `127.0.0.1` on port `3001` and join
with a username. The other tabs let you post a message, list users, and select
or enter a message ID to retrieve its full content. The server can also be
started on another port with `python server.py --port <port>`.
