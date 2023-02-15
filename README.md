# Bulltein Board System

A socket-based BBS system written in Python and SQL.  

hw1 ~ hw3 implements the same system, but with added functionality in newer versions.  

Course: Introduction to Network programming by Shyan-Ming Yuan (NCTU 2020 Fall)

## Features
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
