from typing import TextIO

def build_packet(command: str, *fields: str):
    """
    Builds packet text using the command and its fields.
    
    Args:
        command (str): The first line in the packet that indicates the command, like "POST".
        *fields (str): Zero or more strings for however many command fields the command requires.
    
    Returns:
        str: The packet text with the command and command fields, each separated by a single newline
        character, that ends with two subsequent newline characters.
    """
    return "\n".join([command, *fields]) + "\n\n"

def read_packet(reader: TextIO):
    """
    Reads a packet.

    Args:
        reader (TextIO): Reader wrapped around the connected socket,
            created with sock.makefile("r").
    
    Returns:
        tuple[str, list[str]] | None: The command and the list of fields
            or None if the connection closed.
    """
    # Holds the lines read from a packet.
    lines = []

    while True:
        line = reader.readline()

        # If readline returns "" then we are at the end of the stream, connection closed.
        if line == "":
            return None

        # Take the newline character away, detects blank lines (end of packet according to the protocol).
        line = line.rstrip("\n")

        # End of packet at a blank line.
        if line == "":
            # If there were lines read, return the command (should be the first line read)
            # then return the remaining command fields.
            if lines:
                return lines[0], lines[1:]

        # Continue to build the lines read.
        lines.append(line)