# CS4065 Programming Assignment 2: Bulletin Board

Group members: Colin Davis, Huy Le, Caden Burks-D'amico

## Protocol:

Messages exchanged between the client and server will use a plaintext format.

Each "packet" will begin with the command the client wants to send. From this, the server will expect the remainder of the packet to include the fields that relate to that particular command.

Different fields within a packet will be separated with a single newline character.

The end of a packer will be represented with two subsequent newline characters.
