```markdown
# echomesh

p2p encrypted messenger. no servers. only host gets plugin power.

## what u get

- 🔒 encrypted af (Fernet / AES-128)
- 🚫 no servers - straight p2p
- 👑 admin commands (kick, announce) - host only
- 🔐 password that room
- 📜 message history (last 100)
- ✏️ typing indicator
- 🔌 plugin system (.emf) - host only for safety
- 🎨 clean colored ui

## looks like this

```
[22:15:30] bro: sup
[22:15:32] → not much
[22:15:35] * bro laughs
┌─u ─────────────────────────────────
└> 

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Cryptography](https://img.shields.io/badge/crypto-Fernet-purple.svg)
![Stars](https://img.shields.io/github/stars/klmpt/echomesh?style=social)
![Forks](https://img.shields.io/github/forks/klmpt/echomesh?style=social)

```

## install

```bash
git clone https://github.com/ur_name/echomesh.git
cd echomesh

python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on windows

pip install cryptography

python3 echomesh.py
```

## how to use

### host (create room - u become admin)
```bash
python3 echomesh.py
# pick 1
# set room password if u want
# set admin password if u want (u become the boss)
# give ur ip to the other person
```

### connect (join someone's room)
```bash
python3 echomesh.py
# pick 2
# type their ip
# enter room password if needed
# start yapping
```

## commands

| command | what it does |
|---------|---------------|
| `/quit` | gtfo |
| `/me <text>` | do an action like `/me waves` |
| `/status` | show connection info |
| `/history` | last 15 messages |
| `/help` | this list |

### admin commands (host only)

| command | what it does |
|---------|---------------|
| `/kick` | yeet the peer out |
| `/announce <msg>` | yell at everyone |
| `/plugins` | list loaded plugins |

## plugins

Drop `.emf` files in `plugins/` folder. Example:

```python
# plugins/example.emf
def setup():
    return {
        'name': 'Example Plugin',
        'version': '1.0',
        'description': 'just an example'
    }

def commands():
    return {
        '/ping': ping
    }

def ping(args, ctx):
    return ctx['col']("pong!", ctx['style'].G)
```

**Heads up:** Only the host can load plugins. Clients can't run any plugin code. Safe.

## how this thing works

```
[ur pc] ←─── encrypted ───→ [peer's pc]
     (no servers, no middlemen)
```

- New keys every session
- Each message encrypted separately
- No logs kept forever

## what u need

- Python 3.8+
- cryptography lib (pip installs it)
- Open port 8888 if ur hosting (or change it)

## internet access (not local network)

Use ngrok for outside connections:

```bash
# on host machine
ngrok tcp 8888

# give that ngrok address to ur friend
```

Or RadminVPN on Shitdows:

[Download](https://www.radmin-vpn.com/)

## build that executable

```bash
# with pyinstaller (easy)
pip install pyinstaller
pyinstaller --onefile --console EchoMesh.py

# with nuitka (linux chads)
pip install nuitka
nuitka --standalone --onefile --follow-imports --include-package=cryptography EchoMesh.py
```
