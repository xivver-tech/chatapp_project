# Chat App

A self-hosted, cross-platform (Windows / Linux / Android) chat client built entirely in Python, using the [Matrix](https://matrix.org) protocol for the backend. Inspired by Discord/WhatsApp/Matrix clients — customizable themes, an in-app admin dashboard, message replies, presence, and more.

## Features

- Username/password login and signup (no 2FA)
- Real-time messaging (live sync, no manual refresh)
- Start 1-on-1 chats or create groups
- @mentions with highlighting
- Message replies/quotes
- Online/offline presence indicators
- Customizable theme (accent color, optional gradient background)
- Desktop notifications for new messages
- In-app **Admin Dashboard** (for superuser accounts):
  - Register new users
  - Promote/demote admins
  - Deactivate accounts
  - Reset passwords
  - Kick/ban users from a room
  - Delete (redact) individual messages
  - Purge a room's entire history
- Works against any Matrix homeserver — self-hosted (Synapse) or otherwise

## Requirements

- Python 3.10+
- A running Matrix homeserver (this project is built and tested against [Synapse](https://github.com/element-hq/synapse))

## Installation

### 1. Set up the client

```bash
git clone https://github.com/xivver-tech/chatapp.git
cd chatapp
python3 -m venv chatapp-env
source chatapp-env/bin/activate      # Windows: chatapp-env\Scripts\activate
pip install kivy kivymd matrix-nio requests plyer pillow
```

### 2. Set up a Matrix homeserver (Synapse, via Docker)

If you don't already have a homeserver to connect to:

```bash
mkdir -p ~/synapse-data
docker run -it --rm \
  -v ~/synapse-data:/data \
  -e SYNAPSE_SERVER_NAME=localhost \
  -e SYNAPSE_REPORT_STATS=no \
  matrixdotorg/synapse:latest generate

docker run -d --name synapse -p 8008:8008 -v ~/synapse-data:/data matrixdotorg/synapse:latest
```

Create your first account (say `yes` when asked to make it an admin):

```bash
docker exec -it synapse register_new_matrix_user http://localhost:8008 -c /data/homeserver.yaml
```

### 3. Run the app

```bash
python3 main.py
```

Enter your homeserver URL (`http://localhost:8008` for a local server, or your public URL if hosted elsewhere), your username, and password.

## Making an account a superuser (admin dashboard access)

Superuser status is tracked locally in `users.json`, separate from Matrix's own permissions. To promote your first account:

```bash
python3 -c "
from user_store import add_user
add_user('your_username', 'your_password', is_superuser=True)
"
```

Log in with that account and you'll be sent straight to the Admin Dashboard instead of the normal chat screen. From there you can register and promote other users through the UI — no more manual scripting needed after this first one.

## Using the app

- **New chat / New group**: from the room list, enter another user's username (or full `@user:server` ID) to start a conversation
- **Reply**: tap "Reply" next to any message to quote it in your next message
- **Theme**: change your accent color and toggle a gradient background from the Theme settings screen
- **Clear chat**: clears your own local view of a conversation (does not delete messages for the other person — use the Admin Dashboard's redact/purge tools for that)

## Notes

- This is a personal/self-hosted project, not intended for production use at scale
- Superuser accounts are tracked in `users.json` (kept out of version control — see `.gitignore`)
- Building an Android APK is supported via [Buildozer](https://github.com/kivy/buildozer) (`buildozer.spec` included)
