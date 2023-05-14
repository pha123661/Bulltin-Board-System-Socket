# Bulltein Board System

A socket-based BBS system written in Python and SQL.

## Features

See [Document.pdf](./Document.pdf) for more information.

* Account-related
  * Registration
  * Login/Logout
  * Whoami
  * List online users
* Post-related
  * Create new board
  * List all boards
  * Create new post
  * List all posts
  * Read/Update/Delete post
  * Comment on post
* Chatroom-related
  * Create/Join/Attach the chatroom (Attach is for the chatroom creator, while join is for others)
  * List all chatrooms
  * Chatting simultaneously in the chatroom
  * Get past messages from the chat room when you join
* Supports multiple users with multi-threading
* Supports both TCP and UDP connections

## Deployment

Note: Only works with Linux systems.

Server:
Binds to all ip addresses ("0.0.0.0") in the server

```sh
python server.py {PORT}
```

Client:

```sh
python client.py {SERVER_IP} {SERVER_PORT}
```