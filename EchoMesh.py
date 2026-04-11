#!/usr/bin/env python3
# echomesh - p2p encrypted messenger
# ONLY HOST CAN BE ADMIN

import socket
import threading
import json
import secrets
import time
import sys
import hashlib
import os
from datetime import datetime
from cryptography.fernet import Fernet
import base64

# ------------- colors -------------
class style:
    R = '\033[91m'
    G = '\033[92m'
    Y = '\033[93m'
    B = '\033[94m'
    P = '\033[95m'
    C = '\033[96m'
    W = '\033[97m'
    D = '\033[2m'
    BD = '\033[1m'
    RST = '\033[0m'

def col(txt, c):
    return f"{c}{txt}{style.RST}"

# ------------- banner -------------
BANNER = r'''
▄▀▀█▄▄▄▄  ▄▀▄▄▄▄   ▄▀▀▄ ▄▄   ▄▀▀▀▀▄   ▄▀▀▄ ▄▀▄  ▄▀▀█▄▄▄▄  ▄▀▀▀▀▄  ▄▀▀▄ ▄▄ 
▐  ▄▀   ▐ █ █    ▌ █  █   ▄▀ █      █ █  █ ▀  █ ▐  ▄▀   ▐ █ █   ▐ █  █   ▄▀
  █▄▄▄▄▄  ▐ █      ▐  █▄▄▄█  █      █ ▐  █    █   █▄▄▄▄▄     ▀▄   ▐  █▄▄▄█ 
  █    ▌    █         █   █  ▀▄    ▄▀   █    █    █    ▌  ▀▄   █     █   █ 
 ▄▀▄▄▄▄    ▄▀▄▄▄▄▀   ▄▀  ▄▀    ▀▀▀▀   ▄▀   ▄▀    ▄▀▄▄▄▄    █▀▀▀     ▄▀  ▄▀ 
 █    ▐   █     ▐   █   █             █    █     █    ▐    ▐       █   █   
 ▐        ▐         ▐   ▐             ▐    ▐     ▐                 ▐   ▐   
'''

# ------------- plugin system (host only) -------------
class PluginManager:
    def __init__(self, is_admin=False):
        self.plugins = {}
        self.plugin_dir = "plugins"
        self.is_admin = is_admin
        
        if not os.path.exists(self.plugin_dir) and is_admin:
            os.makedirs(self.plugin_dir)
    
    def load_plugins(self):
        if not self.is_admin:
            print(col("  plugins disabled (only host can use plugins)", style.D))
            return
            
        if not os.path.exists(self.plugin_dir):
            return
            
        for file in os.listdir(self.plugin_dir):
            if file.endswith('.emf'):
                self.load_plugin(file)
    
    def load_plugin(self, filename):
        path = os.path.join(self.plugin_dir, filename)
        name = filename[:-4]
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            module = {}
            exec(code, module)
            
            if 'setup' in module:
                plugin_info = module['setup']()
                self.plugins[name] = {
                    'module': module,
                    'info': plugin_info,
                    'enabled': True
                }
                print(col(f"  ✓ loaded: {plugin_info.get('name', name)}", style.G))
            else:
                print(col(f"  ✗ {name}: no setup() function", style.R))
        except Exception as e:
            print(col(f"  ✗ {name}: {e}", style.R))
    
    def get_commands(self):
        cmds = {}
        for name, p in self.plugins.items():
            if p['enabled'] and 'commands' in p['module']:
                cmds.update(p['module']['commands']())
        return cmds
    
    def execute(self, cmd, args, ctx):
        if not self.is_admin:
            return None
        cmds = self.get_commands()
        if cmd in cmds:
            try:
                return cmds[cmd](args, ctx)
            except Exception as e:
                return col(f"plugin error: {e}", style.R)
        return None

# ------------- main class -------------
class EchoMesh:
    def __init__(self, nick):
        self.nick = nick
        self.sock = None
        self.cipher = None
        self.peer = None
        self.running = True
        self.is_admin = False
        self.room_pass = None
        self.history = []
        self.connected = False
        self.plugin_manager = None

    def banner(self):
        os.system('clear')
        print(col(BANNER, style.C))
        print(col("       p2p encrypted | no bullshit | host only admin", style.D))
        print()

    def local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'

    def send(self, sock, data):
        try:
            j = json.dumps(data)
            b = j.encode()
            sock.send(len(b).to_bytes(4, 'big'))
            sock.send(b)
            return True
        except:
            return False

    def recv(self, sock):
        try:
            l = sock.recv(4)
            if not l: return None
            length = int.from_bytes(l, 'big')
            if length > 1024*1024: return None
            d = b''
            while len(d) < length:
                chunk = sock.recv(min(4096, length - len(d)))
                if not chunk: return None
                d += chunk
            return json.loads(d.decode())
        except:
            return None

    def host(self, port=8888):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        print(col("\n┌─ setup ─────────────────────────────", style.D))
        
        # room password
        pwd = input(col("│ room pass (skip): ", style.Y)).strip()
        if pwd:
            self.room_pass = hashlib.sha256(pwd.encode()).hexdigest()
            print(col("│ room protected with password", style.G))
        
        # admin password - ONLY HOST CAN BE ADMIN
        admin = input(col("│ admin pass (skip): ", style.Y)).strip()
        if admin:
            self.is_admin = True
            print(col("│ YOU ARE THE HOST ADMIN", style.P))
        
        print(col("└────────────────────────────────────", style.D))

        server.bind(('0.0.0.0', port))
        server.listen(1)

        ip = self.local_ip()
        print(col(f"\n► hosting on {ip}:{port}", style.G))
        print(col("► waiting for connection...", style.D))

        self.sock, addr = server.accept()
        self.peer = addr[0]
        print(col(f"► connected to {self.peer}", style.G))

        # password check
        if self.room_pass:
            self.send(self.sock, {'type': 'pass_req'})
            resp = self.recv(self.sock)
            if not resp or resp.get('pass') != self.room_pass:
                self.send(self.sock, {'type': 'error'})
                self.sock.close()
                return False
            self.send(self.sock, {'type': 'pass_ok'})

        # key exchange
        key = Fernet.generate_key()
        self.send(self.sock, {'type': 'key', 'key': base64.b64encode(key).decode()})
        resp = self.recv(self.sock)
        
        if resp and resp.get('type') == 'key_ack':
            self.cipher = Fernet(key)
            # SEND admin=False TO CLIENT - CLIENT NEVER GETS ADMIN
            self.send(self.sock, {'type': 'ready', 'admin': False})
            self.connected = True
            print(col("► secure channel 🔒", style.G))
            
            # plugins only for host
            self.plugin_manager = PluginManager(is_admin=self.is_admin)
            if self.is_admin:
                print(col("\n► loading plugins:", style.D))
                self.plugin_manager.load_plugins()
            
            return True
        return False

    def connect(self, target, port=8888):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((target, port))
            self.peer = target
            print(col(f"► connected to {target}:{port}", style.G))

            # client does NOT enter admin password
            # only room password if needed
            data = self.recv(self.sock)
            if data and data.get('type') == 'pass_req':
                pwd = input(col("room password: ", style.Y)).strip()
                h = hashlib.sha256(pwd.encode()).hexdigest()
                self.send(self.sock, {'type': 'pass', 'pass': h})
                resp = self.recv(self.sock)
                if resp and resp.get('type') == 'error':
                    print(col("► wrong password", style.R))
                    return False
                data = self.recv(self.sock)

            # key exchange
            if data and data.get('type') == 'key':
                k = base64.b64decode(data.get('key'))
                self.cipher = Fernet(k)
                self.send(self.sock, {'type': 'key_ack'})
                ready = self.recv(self.sock)
                
                if ready and ready.get('type') == 'ready':
                    # client receives admin from host (always False)
                    self.is_admin = ready.get('admin', False)
                    self.connected = True
                    print(col("► secure channel 🔒", style.G))
                    
                    if self.is_admin:
                        print(col("► YOU ARE ADMIN (this should never happen)", style.R))
                    else:
                        print(col("► you are regular user (no admin rights)", style.D))
                    
                    # client does NOT get plugins
                    self.plugin_manager = PluginManager(is_admin=False)
                    
                    return True
            return False
        except Exception as e:
            print(col(f"► failed: {e}", style.R))
            return False

    def recv_loop(self):
        while self.running and self.sock:
            try:
                data = self.recv(self.sock)
                if not data:
                    break

                t = data.get('type')

                if t == 'msg':
                    enc = data.get('data', '')
                    if self.cipher and enc:
                        try:
                            dec = self.cipher.decrypt(enc.encode()).decode()
                            sender = data.get('from', '?')
                            ts = datetime.now().strftime('%H:%M:%S')
                            self.history.append((ts, sender, dec))
                            if len(self.history) > 100:
                                self.history.pop(0)

                            sys.stdout.write('\r' + ' ' * 80 + '\r')
                            if sender == self.nick:
                                sys.stdout.write(f"{col(f'[{ts}]', style.D)} {col('→', style.G)} {col(dec, style.G)}\n")
                            else:
                                sys.stdout.write(f"{col(f'[{ts}]', style.B)} {col(sender, style.C)}: {col(dec, style.W)}\n")
                            sys.stdout.write(f"{col('└> ', style.D)}")
                            sys.stdout.flush()
                        except:
                            pass

                elif t == 'action':
                    enc = data.get('data', '')
                    if self.cipher and enc:
                        try:
                            act = self.cipher.decrypt(enc.encode()).decode()
                            sender = data.get('from', '?')
                            ts = datetime.now().strftime('%H:%M:%S')
                            sys.stdout.write('\r' + ' ' * 80 + '\r')
                            if sender == self.nick:
                                sys.stdout.write(f"{col(f'[{ts}]', style.D)} {col('→', style.P)} * {col(act, style.P)}\n")
                            else:
                                sys.stdout.write(f"{col(f'[{ts}]', style.P)} * {col(sender, style.P)} {col(act, style.D)}\n")
                            sys.stdout.write(f"{col('└> ', style.D)}")
                            sys.stdout.flush()
                        except:
                            pass

                elif t == 'announce':
                    msg = data.get('msg', '')
                    sys.stdout.write('\r' + ' ' * 80 + '\r')
                    sys.stdout.write(f"{col('📢', style.Y)} {col(msg, style.C)}\n")
                    sys.stdout.write(f"{col('└> ', style.D)}")
                    sys.stdout.flush()

                elif t == 'kick':
                    sys.stdout.write('\r' + ' ' * 80 + '\r')
                    print(col("► you got kicked by admin", style.R))
                    self.running = False
                    break

                elif t == 'ping':
                    self.send(self.sock, {'type': 'pong'})

            except:
                break

        self.connected = False
        if self.running:
            print(col("\n► connection lost", style.R))
            self.running = False

    def send_msg(self, text):
        if not self.sock or not self.cipher:
            return False
        if not text.strip():
            return False
        try:
            enc = self.cipher.encrypt(text.encode()).decode()
            ok = self.send(self.sock, {'type': 'msg', 'from': self.nick, 'data': enc})
            if ok:
                ts = datetime.now().strftime('%H:%M:%S')
                self.history.append((ts, self.nick, text))
                sys.stdout.write('\r' + ' ' * 80 + '\r')
                sys.stdout.write(f"{col(f'[{ts}]', style.D)} {col('→', style.G)} {col(text, style.G)}\n")
                sys.stdout.write(f"{col('└> ', style.D)}")
                sys.stdout.flush()
            return ok
        except:
            return False

    def send_action(self, text):
        if not self.sock or not self.cipher:
            return False
        try:
            enc = self.cipher.encrypt(text.encode()).decode()
            return self.send(self.sock, {'type': 'action', 'from': self.nick, 'data': enc})
        except:
            return False

    def chat(self):
        if not self.connected:
            print(col("► not connected", style.R))
            return

        threading.Thread(target=self.recv_loop, daemon=True).start()

        print(col("\n┌────────────────────────────────────", style.D))
        print(col(f"│ peer: {self.peer}", style.Y))
        print(col(f"│ u: {self.nick}", style.G))
        
        if self.is_admin:
            print(col("│ ADMIN: YES 👑 (HOST ONLY)", style.P))
        else:
            print(col("│ ADMIN: NO (regular user)", style.D))
        
        if self.plugin_manager and self.plugin_manager.plugins:
            print(col("│ plugins:", style.D))
            for name, p in self.plugin_manager.plugins.items():
                print(col(f"│   {p['info'].get('name', name)} v{p['info'].get('version', '?')}", style.D))
        
        print(col("│ type /help for commands", style.D))
        print(col("└────────────────────────────────────", style.D))
        sys.stdout.write(f"{col('└> ', style.D)}")
        sys.stdout.flush()

        try:
            while self.running:
                msg = sys.stdin.readline().strip()
                if msg is None:
                    continue

                if msg == '/quit':
                    break

                elif msg == '':
                    continue

                elif msg == '/help':
                    print(col("\n  commands:", style.Y))
                    print(col("  /quit       exit chat", style.D))
                    print(col("  /me <txt>   action message", style.D))
                    print(col("  /status     connection info", style.D))
                    print(col("  /history    last 15 messages", style.D))
                    
                    if self.is_admin:
                        print(col("  /plugins    list plugins", style.D))
                        print(col("  /kick       kick peer", style.P))
                        print(col("  /announce   broadcast message", style.P))
                    
                    if self.plugin_manager and self.is_admin:
                        plugin_cmds = self.plugin_manager.get_commands()
                        if plugin_cmds:
                            print(col("\n  plugin commands:", style.Y))
                            for cmd in plugin_cmds.keys():
                                print(col(f"  {cmd}", style.D))
                    
                    sys.stdout.write(f"{col('└> ', style.D)}")
                    sys.stdout.flush()
                    continue

                elif msg == '/status':
                    print(col(f"\n  peer: {self.peer}", style.C))
                    print(col(f"  encryption: active 🔒", style.G))
                    print(col(f"  admin: {'YES 👑' if self.is_admin else 'NO'}", style.P if self.is_admin else style.D))
                    if self.plugin_manager:
                        print(col(f"  plugins: {len(self.plugin_manager.plugins)}", style.D))
                    sys.stdout.write(f"{col('└> ', style.D)}")
                    sys.stdout.flush()
                    continue

                elif msg == '/history':
                    print(col("\n  history:", style.C))
                    if not self.history:
                        print(col("  empty", style.D))
                    for ts, who, what in self.history[-15:]:
                        if who == self.nick:
                            print(f"  {col(ts, style.D)} {col('→', style.G)} {what}")
                        else:
                            print(f"  {col(ts, style.B)} {who}: {what}")
                    sys.stdout.write(f"{col('└> ', style.D)}")
                    sys.stdout.flush()
                    continue

                elif msg == '/plugins' and self.is_admin:
                    print(col("\n  plugins:", style.Y))
                    if not self.plugin_manager or not self.plugin_manager.plugins:
                        print(col("  no plugins loaded", style.D))
                        print(col("  put .emf files in ./plugins/", style.D))
                    for name, p in self.plugin_manager.plugins.items():
                        info = p['info']
                        print(col(f"  {info.get('name', name)} v{info.get('version', '?')}", style.G))
                        print(col(f"    {info.get('description', 'no desc')}", style.D))
                    sys.stdout.write(f"{col('└> ', style.D)}")
                    sys.stdout.flush()
                    continue

                elif msg.startswith('/me '):
                    self.send_action(msg[4:])
                    continue

                elif msg == '/kick' and self.is_admin:
                    self.send(self.sock, {'type': 'kick'})
                    print(col("► peer kicked", style.G))
                    continue

                elif msg.startswith('/announce ') and self.is_admin:
                    announcement = msg[10:]
                    self.send(self.sock, {'type': 'announce', 'msg': announcement})
                    print(col(f"► announcement sent", style.G))
                    continue

                else:
                    # plugin commands (only host/admin)
                    if self.plugin_manager and self.is_admin:
                        parts = msg.split(' ')
                        cmd = parts[0]
                        args = ' '.join(parts[1:]) if len(parts) > 1 else ''
                        
                        ctx = {
                            'nick': self.nick,
                            'peer': self.peer,
                            'is_admin': self.is_admin,
                            'send_msg': self.send_msg,
                            'send_action': self.send_action,
                            'history': self.history,
                            'col': col,
                            'style': style
                        }
                        
                        result = self.plugin_manager.execute(cmd, args, ctx)
                        if result is not None:
                            if result:
                                print(result)
                            sys.stdout.write(f"{col('└> ', style.D)}")
                            sys.stdout.flush()
                            continue
                    
                    # normal message
                    self.send_msg(msg)

        except KeyboardInterrupt:
            pass

        self.running = False
        if self.sock:
            self.sock.close()
        print(col("\n► disconnected", style.R))

def main():
    chat = EchoMesh("")
    chat.banner()

    nick = input(col("nickname: ", style.C)).strip()
    if not nick:
        nick = f"user_{secrets.token_hex(2)}"
    chat.nick = nick

    print()
    print(col("  1. host (create room - you become admin)", style.G))
    print(col("  2. connect (join room - regular user)", style.B))
    print(col("  3. exit", style.R))
    print()

    choice = input(col("> ", style.Y)).strip()

    if choice == '1':
        port = input(col("port (8888): ", style.D)).strip()
        port = int(port) if port else 8888
        if chat.host(port):
            chat.chat()
        else:
            print(col("► failed", style.R))

    elif choice == '2':
        ip = input(col("target ip: ", style.D)).strip()
        port = input(col("port (8888): ", style.D)).strip()
        port = int(port) if port else 8888
        if chat.connect(ip, port):
            chat.chat()
        else:
            print(col("► failed", style.R))

    elif choice == '3':
        print(col("► bye", style.D))

if __name__ == "__main__":
    main()
