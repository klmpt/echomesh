#!/usr/bin/env python3
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
from collections import defaultdict

class EchoMeshPro:
    def __init__(self, nickname: str):
        self.nickname = nickname
        self.connection = None
        self.cipher = None
        self.peer_addr = None
        self.running = True
        self.is_host = False
        self.is_admin = False
        self.room_password = None
        self.admin_password = None
        self.banned_ips = set()
        self.message_history = []
        self.rate_limit = defaultdict(list)
        
        self.stats = {
            'sent': 0,
            'received': 0,
        }
    
    def color_text(self, text, color):
        colors = {
            'red': '\033[91m', 'green': '\033[92m', 'yellow': '\033[93m',
            'blue': '\033[94m', 'purple': '\033[95m', 'cyan': '\033[96m',
            'white': '\033[97m', 'bold': '\033[1m', 'dim': '\033[2m',
            'magenta': '\033[95m',
            'reset': '\033[0m'
        }
        return f"{colors.get(color, '')}{text}{colors['reset']}"
    
    def print_banner(self):
        banner = f"""
{self.color_text('╔══════════════════════════════════════════════════════════╗', 'cyan')}
{self.color_text('║', 'cyan')}              {self.color_text('🌟 ECHOMESH PRO v3.1 🌟', 'bold')}                  {self.color_text('║', 'cyan')}
{self.color_text('║', 'cyan')}         {self.color_text('Clean P2P Encrypted Messenger', 'white')}                {self.color_text('║', 'cyan')}
{self.color_text('╚══════════════════════════════════════════════════════════╝', 'cyan')}
        """
        print(banner)
    
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    def send_json(self, sock, data):
        try:
            json_str = json.dumps(data)
            json_bytes = json_str.encode('utf-8')
            length = len(json_bytes)
            sock.send(length.to_bytes(4, 'big'))
            sock.send(json_bytes)
            return True
        except:
            return False
    
    def recv_json(self, sock):
        try:
            length_data = sock.recv(4)
            if not length_data:
                return None
            length = int.from_bytes(length_data, 'big')
            if length > 1024 * 1024:
                return None
            data = b''
            while len(data) < length:
                chunk = sock.recv(min(4096, length - len(data)))
                if not chunk:
                    return None
                data += chunk
            return json.loads(data.decode('utf-8'))
        except:
            return None
    
    def start_host(self, port=8888):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            print(f"\n{self.color_text('🔧 ROOM SETUP', 'cyan')}")
            print(f"{self.color_text('─' * 40, 'white')}")
            
            set_password = input(self.color_text("🔒 Set room password? (y/n): ", 'yellow')).lower()
            if set_password == 'y':
                self.room_password = hashlib.sha256(
                    input(self.color_text("📝 Password: ", 'yellow')).encode()
                ).hexdigest()
                print(self.color_text("✅ Password protected!", 'green'))
            
            set_admin = input(self.color_text("👑 Set admin password? (y/n): ", 'yellow')).lower()
            if set_admin == 'y':
                self.admin_password = hashlib.sha256(
                    input(self.color_text("🔐 Admin password: ", 'yellow')).encode()
                ).hexdigest()
                self.is_admin = True
                print(self.color_text("✅ You are the HOST admin!", 'purple'))
            
            server.bind(('0.0.0.0', port))
            server.listen(1)
            my_ip = self.get_local_ip()
            
            print(f"\n{self.color_text('='*50, 'cyan')}")
            print(f"{self.color_text('📡 Hosting on port:', 'yellow')} {port}")
            print(f"{self.color_text('📍 Your IP:', 'yellow')} {self.color_text(my_ip, 'green')}")
            print(f"{self.color_text('⏳ Waiting for connection...', 'yellow')}")
            print(f"{self.color_text('='*50, 'cyan')}\n")
            
            self.connection, addr = server.accept()
            self.peer_addr = addr[0]
            self.is_host = True
            
            if self.peer_addr in self.banned_ips:
                self.send_json(self.connection, {'type': 'error', 'msg': 'You are banned'})
                self.connection.close()
                return False
            
            print(self.color_text(f"✅ Connected to {self.peer_addr}", 'green'))
            
            if self.room_password:
                self.send_json(self.connection, {'type': 'need_password'})
                resp = self.recv_json(self.connection)
                if not resp or resp.get('password') != self.room_password:
                    self.send_json(self.connection, {'type': 'error', 'msg': 'Wrong password'})
                    self.connection.close()
                    return False
                self.send_json(self.connection, {'type': 'password_ok'})
            
            my_key = Fernet.generate_key()
            self.send_json(self.connection, {'type': 'key', 'key': base64.b64encode(my_key).decode()})
            
            resp = self.recv_json(self.connection)
            if resp and resp.get('type') == 'key_ack':
                self.cipher = Fernet(my_key)
                self.send_json(self.connection, {'type': 'ready', 'admin': False})
                print(self.color_text("🔐 Secure channel established!", 'green'))
                return True
            
            return False
        except Exception as e:
            print(self.color_text(f"❌ Host error: {e}", 'red'))
            return False
    
    def connect_to_peer(self, target_ip, port=8888):
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((target_ip, port))
            self.peer_addr = target_ip
            self.is_host = False
            
            print(self.color_text(f"✅ Connected to {target_ip}:{port}", 'green'))
            
            data = self.recv_json(self.connection)
            if data and data.get('type') == 'need_password':
                print(self.color_text("🔒 Room is password protected", 'yellow'))
                pwd = input(self.color_text("📝 Enter password: ", 'yellow'))
                hashed = hashlib.sha256(pwd.encode()).hexdigest()
                self.send_json(self.connection, {'type': 'password', 'password': hashed})
                
                resp = self.recv_json(self.connection)
                if resp and resp.get('type') == 'error':
                    print(self.color_text("❌ Wrong password!", 'red'))
                    return False
                data = self.recv_json(self.connection)
            
            if data and data.get('type') == 'key':
                peer_key = base64.b64decode(data.get('key'))
                self.cipher = Fernet(peer_key)
                self.send_json(self.connection, {'type': 'key_ack'})
                
                ready = self.recv_json(self.connection)
                if ready and ready.get('type') == 'ready':
                    self.is_admin = ready.get('admin', False)
                    print(self.color_text("🔐 Secure channel established!", 'green'))
                    if self.is_admin:
                        print(self.color_text("👑 You are a room admin!", 'purple'))
                    return True
            
            return False
        except Exception as e:
            print(self.color_text(f"❌ Connect error: {e}", 'red'))
            return False
    
    def print_prompt(self):
        sys.stdout.write(f"\r{self.color_text('┌─', 'dim')}{self.color_text(self.nickname, 'yellow')}{self.color_text(' ─────────────────────────────────', 'dim')}\n")
        sys.stdout.write(f"{self.color_text('└> ', 'dim')}")
        sys.stdout.flush()
    
    def display_message(self, sender, message, is_own=False, msg_type='text'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        
        if msg_type == 'action':
            if is_own:
                sys.stdout.write(f"{self.color_text(f'[{timestamp}]', 'dim')} {self.color_text('→', 'purple')} * {self.color_text(message, 'purple')}\n")
            else:
                sys.stdout.write(f"{self.color_text(f'[{timestamp}]', 'purple')} * {self.color_text(sender, 'magenta')} {self.color_text(message, 'dim')}\n")
        else:
            if is_own:
                sys.stdout.write(f"{self.color_text(f'[{timestamp}]', 'dim')} {self.color_text('→', 'green')} {self.color_text(message, 'green')}\n")
            else:
                sys.stdout.write(f"{self.color_text(f'[{timestamp}]', 'blue')} {self.color_text(sender, 'cyan')}: {self.color_text(message, 'white')}\n")
        
        sys.stdout.write(f"{self.color_text('┌─', 'dim')}{self.color_text(self.nickname, 'yellow')}{self.color_text(' ─────────────────────────────────', 'dim')}\n")
        sys.stdout.write(f"{self.color_text('└> ', 'dim')}")
        sys.stdout.flush()
    
    def receive_loop(self):
        while self.running and self.connection:
            try:
                data = self.recv_json(self.connection)
                if not data:
                    break
                
                msg_type = data.get('type')
                
                if msg_type == 'message':
                    encrypted = data.get('data', '')
                    if self.cipher and encrypted:
                        try:
                            decrypted = self.cipher.decrypt(encrypted.encode()).decode()
                            sender = data.get('sender', '?')
                            
                            self.stats['received'] += 1
                            self.message_history.append((datetime.now(), sender, decrypted))
                            if len(self.message_history) > 100:
                                self.message_history.pop(0)
                            
                            self.display_message(sender, decrypted, is_own=False)
                        except:
                            pass
                
                elif msg_type == 'action':
                    encrypted = data.get('data', '')
                    if self.cipher and encrypted:
                        try:
                            action = self.cipher.decrypt(encrypted.encode()).decode()
                            sender = data.get('sender', '?')
                            self.display_message(sender, action, is_own=False, msg_type='action')
                        except:
                            pass
                
                elif msg_type == 'announcement':
                    msg = data.get('msg', '')
                    sys.stdout.write('\r' + ' ' * 80 + '\r')
                    sys.stdout.write(f"{self.color_text('📢', 'yellow')} {self.color_text(msg, 'cyan')}\n")
                    self.print_prompt()
                
                elif msg_type == 'system':
                    msg = data.get('msg', '')
                    sys.stdout.write('\r' + ' ' * 80 + '\r')
                    sys.stdout.write(f"{self.color_text('🔔', 'red')} {msg}\n")
                    self.print_prompt()
                
                elif msg_type == 'kick':
                    sys.stdout.write('\r' + ' ' * 80 + '\r')
                    print(f"{self.color_text('❌ You have been kicked by admin', 'red')}")
                    self.running = False
                    break
                
                elif msg_type == 'typing':
                    if data.get('is_typing'):
                        sys.stdout.write('\r' + ' ' * 80 + '\r')
                        sys.stdout.write(f"{self.color_text('✏️ Peer is typing...', 'yellow')}\n")
                        self.print_prompt()
                
                elif msg_type == 'ping':
                    self.send_json(self.connection, {'type': 'pong'})
                    
            except Exception as e:
                break
        
        print(f"\n{self.color_text('🔌 Disconnected', 'red')}")
        self.running = False
    
    def send_message(self, text):
        if not self.connection or not self.cipher:
            return False
        try:
            encrypted = self.cipher.encrypt(text.encode()).decode()
            success = self.send_json(self.connection, {'type': 'message', 'sender': self.nickname, 'data': encrypted})
            if success:
                self.stats['sent'] += 1
                self.message_history.append((datetime.now(), self.nickname, text))
                self.display_message(self.nickname, text, is_own=True)
            return success
        except:
            return False
    
    def send_action(self, action):
        if not self.connection or not self.cipher:
            return False
        try:
            encrypted = self.cipher.encrypt(action.encode()).decode()
            success = self.send_json(self.connection, {'type': 'action', 'sender': self.nickname, 'data': encrypted})
            if success:
                self.display_message(self.nickname, action, is_own=True, msg_type='action')
            return success
        except:
            return False
    
    def send_typing(self, is_typing):
        if not self.connection:
            return
        self.send_json(self.connection, {'type': 'typing', 'is_typing': is_typing})
    
    def chat_loop(self):
        if not self.connection or not self.cipher:
            print(self.color_text("❌ Not connected", 'red'))
            return
        
        recv_thread = threading.Thread(target=self.receive_loop)
        recv_thread.daemon = True
        recv_thread.start()
        
        print(f"\n{self.color_text('='*50, 'cyan')}")
        print(f"{self.color_text('💬 CHAT ACTIVE', 'bold')}")
        print(f"{self.color_text('📡 Peer:', 'yellow')} {self.peer_addr}")
        print(f"{self.color_text('👤 You:', 'yellow')} {self.color_text(self.nickname, 'green')}")
        print(f"{self.color_text('👑 Admin:', 'yellow')} {self.color_text('Yes' if self.is_admin else 'No', 'purple' if self.is_admin else 'white')}")
        print(f"{self.color_text('='*50, 'cyan')}")
        print(f"{self.color_text('Commands:', 'yellow')} /help, /quit, /me, /status, /history")
        if self.is_admin:
            print(f"{self.color_text('Admin:', 'purple')} /kick, /announce <msg>")
        print(f"{self.color_text('='*50, 'cyan')}\n")
        

        self.print_prompt()
        
        try:
            while self.running:
                try:
                    message = sys.stdin.readline().strip()
                    
                    if not message:
                        continue
                    
                    if message.lower() == '/quit':
                        print(self.color_text("👋 Disconnecting...", 'yellow'))
                        break
                    
                    elif message.lower() == '/help':
                        print(f"\n{self.color_text('📋 COMMANDS:', 'yellow')}")
                        print(f"  {self.color_text('/quit', 'red')}     - Exit chat")
                        print(f"  {self.color_text('/me', 'green')}      - Action: /me waves")
                        print(f"  {self.color_text('/status', 'cyan')}   - Show connection info")
                        print(f"  {self.color_text('/history', 'blue')}  - Last 15 messages")
                        if self.is_admin:
                            print(f"  {self.color_text('/kick', 'red')}     - Kick peer")
                            print(f"  {self.color_text('/announce', 'purple')} - Send announcement")
                        self.print_prompt()
                        continue
                    
                    elif message.lower() == '/status':
                        print(f"\n{self.color_text('📊 STATUS', 'cyan')}")
                        print(f"  {self.color_text('Peer:', 'yellow')} {self.peer_addr}")
                        print(f"  {self.color_text('Sent:', 'yellow')} {self.stats['sent']}")
                        print(f"  {self.color_text('Received:', 'yellow')} {self.stats['received']}")
                        print(f"  {self.color_text('Admin:', 'yellow')} {'Yes' if self.is_admin else 'No'}")
                        self.print_prompt()
                        continue
                    
                    elif message.lower() == '/history':
                        print(f"\n{self.color_text('📜 LAST MESSAGES', 'cyan')}")
                        if not self.message_history:
                            print(f"  {self.color_text('No messages yet', 'white')}")
                        for dt, s, m in self.message_history[-15:]:
                            ts = dt.strftime('%H:%M:%S')
                            if s == self.nickname:
                                print(f"  {self.color_text(f'[{ts}]', 'dim')} {self.color_text('→', 'green')} {self.color_text(m, 'green')}")
                            else:
                                print(f"  {self.color_text(f'[{ts}]', 'blue')} {self.color_text(s, 'cyan')}: {self.color_text(m, 'white')}")
                        self.print_prompt()
                        continue
                    
                    elif message.startswith('/me '):
                        action_text = message[4:]
                        self.send_action(action_text)
                        continue
                    
                    elif message.lower() == '/kick' and self.is_admin:
                        self.send_json(self.connection, {'type': 'kick'})
                        print(self.color_text("✅ Peer kicked", 'green'))
                        self.print_prompt()
                        continue
                    
                    elif message.startswith('/announce ') and self.is_admin:
                        announcement = message[10:]
                        self.send_json(self.connection, {'type': 'announcement', 'msg': announcement})
                        print(self.color_text(f"📢 Announcement sent", 'green'))
                        self.print_prompt()
                        continue
                    
                    else:
                        self.send_message(message)
                    

                    self.send_typing(True)
                    time.sleep(0.5)
                    self.send_typing(False)
                    
                except EOFError:
                    break
                    
        except KeyboardInterrupt:
            print(f"\n{self.color_text('👋 Interrupted', 'yellow')}")
        finally:
            self.send_typing(False)
            self.running = False
            if self.connection:
                self.connection.close()
            print(self.color_text("✅ Disconnected", 'green'))

def main():
    while True:
        os.system('clear' if sys.platform != 'win32' else 'cls')
        
        chat = EchoMeshPro("")
        chat.print_banner()
        
        nickname = input(f"{chat.color_text('👤 Your nickname:', 'cyan')} ").strip()
        if not nickname:
            nickname = f"User_{secrets.token_hex(2)}"
        chat.nickname = nickname
        
        print(f"\n{chat.color_text('📡 Select mode:', 'yellow')}")
        print(f"  {chat.color_text('1. 🏠 HOST', 'green')} - Create a room (you become admin)")
        print(f"  {chat.color_text('2. 🔌 CONNECT', 'blue')} - Join a room (regular user)")
        print(f"  {chat.color_text('3. ❌ EXIT', 'red')} - Exit")
        
        choice = input(f"\n{chat.color_text('👉 Choose (1/2/3):', 'yellow')} ").strip()
        
        if choice == '1':
            port_input = input(f"{chat.color_text('🔌 Port (default 8888):', 'cyan')} ").strip()
            port = int(port_input) if port_input else 8888
            
            if chat.start_host(port):
                chat.chat_loop()
            else:
                input(f"\n{chat.color_text('Press Enter to continue...', 'white')}")
                
        elif choice == '2':
            target_ip = input(f"{chat.color_text('🎯 Target IP:', 'cyan')} ").strip()
            port_input = input(f"{chat.color_text('🔌 Port (default 8888):', 'cyan')} ").strip()
            port = int(port_input) if port_input else 8888
            
            if chat.connect_to_peer(target_ip, port):
                chat.chat_loop()
            else:
                input(f"\n{chat.color_text('Press Enter to continue...', 'white')}")
                
        elif choice == '3':
            print(chat.color_text("👋 Goodbye!", 'cyan'))
            break
        else:
            print(chat.color_text("❌ Invalid choice", 'red'))
            time.sleep(1)

if __name__ == "__main__":
    main()
