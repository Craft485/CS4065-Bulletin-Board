# CS4065 Project 2: Bulletin Board Deliverables Checklist

## Preamble: General Project Requirements

### Technical constraints

- [ ] Implement a client and a standalone server, using Java, Python, and/or C/C++
- [ ] Use only raw sockets for networking, with no other built-in or third-party networking libraries
- [ ] Use unicast sockets only (the server tracks all connected client sockets)
- [ ] *(Optional, about +5%)* Write the client and server in different languages
- [ ] *(Optional, up to +5%)* Build a GUI client
- [ ] Submit one common codebase in which Parts 1 and 2 work together in the same process run. Users must be able to switch between the two parts without disconnecting from the server.

### Protocol and server architecture

- [ ] Design and document a client-server protocol (plain text, XML, or JSON) with a format both sides can parse
- [ ] Use one thread per TCP connection (similar to the Project 1 multithreaded web server)
- [ ] Keep each TCP connection open until the client leaves the group and disconnects from the server
- [ ] Listen on a non-system port (above 1023)

### Documentation (15%)

- [ ] Comment the code and use expressive variable names
- [ ] Write a README with:
  - [x] Names of all group members at the very top
  - [ ] Compile and run instructions for the server and client, including any required software or packages
  - [ ] Usability instructions, only where they differ from the suggested commands
  - [ ] A description of major issues encountered and how they were handled, or why they weren't

## Part 1: Public Message Board (40% of functionality)

### Server

- [ ] Run as a standalone process that listens endlessly on a fixed port
- [ ] Treat all clients as members of one public group
- [ ] Prompt each joining client for a user name and reject names already in use (no authentication required)
- [ ] Track users as they join and leave the group
- [ ] Notify all other connected clients when a user joins
- [ ] Notify all other connected clients when a user leaves
- [ ] When a user joins, send them the list of users already in the group
- [ ] When a user joins, send them only the last 2 messages posted before they joined
- [ ] When a user posts, deliver the message to the other users in the group
- [ ] Store messages with a unique ID, sender, post date, subject, and content
- [ ] Display each message in the format `Message ID, Sender, Post Date, Subject` (content not included)
- [ ] On request, return the full content of a message given its ID

### Client

- [ ] `%connect <address> <port>`: connect to a running server
- [ ] `%join`: join the public board
- [ ] `%post <subject> <content>`: post a message
- [ ] `%users`: list users in the group
- [ ] `%message <id>`: retrieve a message's content
- [ ] `%leave`: leave the group
- [ ] `%exit`: disconnect from the server and quit the client
- [ ] Display incoming notifications and posts from other users as they arrive
- [ ] Handle invalid input and errors gracefully (bad ID, duplicate name, not connected, and so on)

## Part 2: Multiple Private Message Boards (30% of functionality)

### Server

- [ ] After a client connects, provide a list of 5 predefined groups
- [ ] Let users select a group by ID or by name
- [ ] Let a user be a member of multiple groups at the same time
- [ ] Keep users, messages, and notifications isolated per group (members of one group can't see another group's users or messages)
- [ ] Apply the Part 1 behaviors per group: join and leave notifications, user list on join, last 2 messages on join, post delivery, and message retrieval by ID
- [ ] Keep a separate message board and message ID space for each group (or document an alternative design)

### Client

- [ ] `%groups`: list all joinable groups
- [ ] `%groupjoin <id|name>`: join a group
- [ ] `%grouppost <id|name> <subject> <content>`: post to a specific group's board
- [ ] `%groupusers <id|name>`: list users in a group
- [ ] `%groupleave <id|name>`: leave a specific group
- [ ] `%groupmessage <id|name> <message-id>`: retrieve a message from a specific group's board
- [ ] Make notifications and posts show which group they belong to
- [ ] Handle invalid input (unknown group, not a member, and so on)

## Grading Map (50 points)

| Category | Weight | Covered by |
| --- | --- | --- |
| Functionality | 70% (40% Part 1, 30% Part 2) | Part 1 and Part 2 sections |
| Usability | 15% | Command sets, error handling, optional GUI |
| Documentation | 15% | Preamble: code comments, README, Makefile |
