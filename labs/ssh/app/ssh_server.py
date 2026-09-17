import os
import sys
import time
import socket
import threading
import logging
import uuid
import datetime
from typing import Optional, Dict, Any

import paramiko
from paramiko import RSAKey, ServerInterface, AUTH_SUCCESSFUL, AUTH_FAILED, OPEN_SUCCEEDED

import database

logger = logging.getLogger("ssh_server")

HOST_KEY_FILE = os.environ.get("SSH_HOST_KEY_PATH", "/tmp/dadiwoo_ssh_host_rsa.key")

def get_or_create_host_key() -> RSAKey:
    if os.path.exists(HOST_KEY_FILE):
        try:
            return RSAKey(filename=HOST_KEY_FILE)
        except Exception:
            pass
    key = RSAKey.generate(2048)
    key.write_private_key_file(HOST_KEY_FILE)
    return key

class DadiwooSSHServerInterface(ServerInterface):
    def __init__(self, client_ip: str, client_port: int):
        self.client_ip = client_ip
        self.client_port = client_port
        self.authenticated_user: Optional[Dict[str, Any]] = None
        self.auth_method: str = "none"
        self.event = threading.Event()

    def check_ip_fail2ban(self) -> bool:
        conn = database.get_db_connection()
        settings = dict(conn.execute("SELECT * FROM ssh_settings WHERE id = 1").fetchone())
        if not settings["fail2ban_enabled"]:
            conn.close()
            return True

        row = conn.execute("SELECT * FROM ssh_fail2ban WHERE ip_address = ?", (self.client_ip,)).fetchone()
        if row and row["failed_attempts"] >= settings["max_failed_attempts"]:
            # Check if ban expired
            banned_until = row["banned_until"]
            if banned_until:
                ban_time = datetime.datetime.fromisoformat(banned_until) if isinstance(banned_until, str) else banned_until
                if datetime.datetime.now() < ban_time:
                    conn.close()
                    logger.warning(f"SSH Connection rejected for banned IP {self.client_ip}")
                    return False
                else:
                    conn.execute("UPDATE ssh_fail2ban SET failed_attempts = 0, banned_until = NULL WHERE ip_address = ?", (self.client_ip,))
                    conn.commit()
        conn.close()
        return True

    def record_failed_attempt(self, username: str, auth_method: str, reason: str):
        conn = database.get_db_connection()
        settings = dict(conn.execute("SELECT * FROM ssh_settings WHERE id = 1").fetchone())

        conn.execute("""
            INSERT INTO ssh_audit_logs (client_ip, username, auth_method, status, details)
            VALUES (?, ?, ?, 'FAILED', ?)
        """, (self.client_ip, username, auth_method, reason))

        if settings["fail2ban_enabled"]:
            row = conn.execute("SELECT * FROM ssh_fail2ban WHERE ip_address = ?", (self.client_ip,)).fetchone()
            if row:
                attempts = row["failed_attempts"] + 1
                banned_until = None
                if attempts >= settings["max_failed_attempts"]:
                    banned_until = (datetime.datetime.now() + datetime.timedelta(seconds=settings["ban_duration_seconds"])).isoformat()
                    logger.warning(f"IP {self.client_ip} has been BANNED by Fail2Ban for {settings['ban_duration_seconds']}s")
                conn.execute("""
                    UPDATE ssh_fail2ban
                    SET failed_attempts = ?, banned_until = ?, last_attempt = CURRENT_TIMESTAMP
                    WHERE ip_address = ?
                """, (attempts, banned_until, self.client_ip))
            else:
                conn.execute("""
                    INSERT INTO ssh_fail2ban (ip_address, failed_attempts, last_attempt)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                """, (self.client_ip,))

        conn.commit()
        conn.close()

    def record_successful_auth(self, username: str, auth_method: str, user_dict: Dict[str, Any]):
        conn = database.get_db_connection()
        conn.execute("""
            INSERT INTO ssh_audit_logs (client_ip, username, auth_method, status, details)
            VALUES (?, ?, ?, 'SUCCESS', 'Authentication successful')
        """, (self.client_ip, username, auth_method))

        # Reset Fail2ban on successful login
        conn.execute("UPDATE ssh_fail2ban SET failed_attempts = 0, banned_until = NULL WHERE ip_address = ?", (self.client_ip,))
        conn.commit()
        conn.close()

        self.authenticated_user = user_dict
        self.auth_method = auth_method

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if not self.check_ip_fail2ban():
            return AUTH_FAILED

        conn = database.get_db_connection()
        settings = dict(conn.execute("SELECT * FROM ssh_settings WHERE id = 1").fetchone())

        if not settings["password_auth_enabled"]:
            conn.close()
            self.record_failed_attempt(username, "password", "Password authentication disabled by server policy")
            return AUTH_FAILED

        user = conn.execute("SELECT * FROM ssh_users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and user["password"] == password:
            self.record_successful_auth(username, "password", dict(user))
            return AUTH_SUCCESSFUL
        else:
            self.record_failed_attempt(username, "password", "Invalid username or password")
            return AUTH_FAILED

    def check_auth_publickey(self, username, key):
        if not self.check_ip_fail2ban():
            return AUTH_FAILED

        conn = database.get_db_connection()
        settings = dict(conn.execute("SELECT * FROM ssh_settings WHERE id = 1").fetchone())

        if not settings["pubkey_auth_enabled"]:
            conn.close()
            self.record_failed_attempt(username, "publickey", "Publickey authentication disabled by server policy")
            return AUTH_FAILED

        user = conn.execute("SELECT * FROM ssh_users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and user["public_key"]:
            # Accept public key matching
            self.record_successful_auth(username, "publickey", dict(user))
            return AUTH_SUCCESSFUL
        else:
            self.record_failed_attempt(username, "publickey", "Publickey not authorized for user")
            return AUTH_FAILED

    def get_allowed_auths(self, username):
        conn = database.get_db_connection()
        settings = dict(conn.execute("SELECT * FROM ssh_settings WHERE id = 1").fetchone())
        conn.close()

        allowed = []
        if settings["password_auth_enabled"]:
            allowed.append("password")
        if settings["pubkey_auth_enabled"]:
            allowed.append("publickey")
        return ",".join(allowed)

    def check_channel_pty_request(self, channel, term, modes, width, height, pixelwidth, pixelheight):
        return True

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

class SSHServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 2222):
        self.host = host
        self.port = port
        self.host_key = get_or_create_host_key()
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.thread: Optional[threading.Thread] = None

    def execute_command_shell(self, chan, user: Dict[str, Any], client_ip: str, session_id: str):
        username = user["username"]
        role = user["role"]
        home_dir = user["home_dir"]
        shell = user["shell"]
        ctf_flag = user["ctf_flag"]

        chan.send(f"\r\n=== Welcome to Dadiwoo Cyber Range Hardened SSH Gateway ===\r\n")
        chan.send(f"Logged in as: {username} ({role})\r\n")
        chan.send(f"System: Linux dadiwoo-range 6.8.0-generic x86_64\r\n")
        chan.send(f"Type 'help' for available commands.\r\n\r\n")

        prompt = f"{username}@dadiwoo-ssh:~# " if role == "admin" else f"{username}@dadiwoo-ssh:~$ "
        chan.send(prompt)

        cmd_buffer = ""
        while True:
            try:
                data = chan.recv(1024)
                if not data:
                    break

                for char in data.decode('utf-8', errors='ignore'):
                    if char in ('\r', '\n'):
                        chan.send('\r\n')
                        cmd = cmd_buffer.strip()
                        cmd_buffer = ""

                        if not cmd:
                            chan.send(prompt)
                            continue

                        # Log command
                        conn = database.get_db_connection()
                        conn.execute("""
                            INSERT INTO ssh_audit_logs (client_ip, username, auth_method, status, command, details)
                            VALUES (?, ?, 'shell', 'EXEC', ?, 'Executed interactive shell command')
                        """, (client_ip, username, cmd))
                        conn.execute("UPDATE ssh_sessions SET commands_count = commands_count + 1 WHERE session_id = ?", (session_id,))
                        conn.commit()
                        conn.close()

                        cmd_parts = cmd.split()
                        base_cmd = cmd_parts[0].lower()

                        if base_cmd in ['exit', 'quit', 'logout']:
                            chan.send("Goodbye!\r\n")
                            chan.close()
                            return

                        elif base_cmd == 'help':
                            chan.send("Available Commands:\r\n")
                            chan.send("  help       - Show command help\r\n")
                            chan.send("  ls         - List directory files\r\n")
                            chan.send("  cat <file> - Read file contents\r\n")
                            chan.send("  whoami     - Show current user\r\n")
                            chan.send("  id         - Show user and group IDs\r\n")
                            chan.send("  uname -a   - System kernel details\r\n")
                            chan.send("  sudo -l    - Check sudo privileges\r\n")
                            chan.send("  pwd        - Print working directory\r\n")
                            chan.send("  flag       - Retrieve CTF flag\r\n")
                            chan.send("  exit       - Close SSH session\r\n")

                        elif base_cmd == 'ls':
                            if role == 'admin':
                                chan.send("root.txt  flag.txt  config.json  id_rsa\r\n")
                            elif role == 'user':
                                chan.send("user.txt  id_rsa  id_rsa.pub  notes.txt\r\n")
                            else:
                                chan.send("guest_notice.txt\r\n")

                        elif base_cmd == 'cat':
                            file_target = cmd_parts[1] if len(cmd_parts) > 1 else ""
                            if 'flag' in file_target or 'root.txt' in file_target:
                                chan.send(f"CTF FLAG: {ctf_flag}\r\n")
                            elif file_target == 'id_rsa':
                                conn = database.get_db_connection()
                                key_row = conn.execute("SELECT private_key_pem FROM ssh_keys WHERE username = ?", (username,)).fetchone()
                                conn.close()
                                if key_row:
                                    chan.send(f"{key_row['private_key_pem']}\r\n")
                                else:
                                    chan.send("No private key found.\r\n")
                            elif file_target == 'user.txt':
                                chan.send("Welcome Standard User! Your flag is in CTF records.\r\n")
                            else:
                                chan.send(f"cat: {file_target}: No such file or directory\r\n")

                        elif base_cmd == 'whoami':
                            chan.send(f"{username}\r\n")

                        elif base_cmd == 'id':
                            if role == 'admin':
                                chan.send("uid=0(root) gid=0(root) groups=0(root)\r\n")
                            elif role == 'user':
                                chan.send("uid=1000(user) gid=1000(user) groups=1000(user),27(sudo)\r\n")
                            else:
                                chan.send("uid=1001(guest) gid=1001(guest) groups=1001(guest)\r\n")

                        elif base_cmd == 'uname':
                            chan.send("Linux dadiwoo-cyber-range 6.8.0-40-generic #40-Ubuntu SMP PREEMPT_DYNAMIC x86_64 GNU/Linux\r\n")

                        elif base_cmd == 'pwd':
                            chan.send(f"{home_dir}\r\n")

                        elif base_cmd in ['sudo', 'sudo -l']:
                            if 'sudo' in cmd:
                                if role == 'user':
                                    chan.send("User user may run the following commands on dadiwoo-range:\r\n")
                                    chan.send("    (ALL : ALL) NOPASSWD: ALL\r\n")
                                    chan.send(f"Escalated to Root! Flag: FLAG{{SSH_SUDO_PRIVILEGE_ESCALATION_EXPLOITED_2026}}\r\n")
                                else:
                                    chan.send("sudo: permission denied\r\n")

                        elif base_cmd == 'flag':
                            chan.send(f"CTF FLAG: {ctf_flag}\r\n")

                        else:
                            chan.send(f"{base_cmd}: command not found\r\n")

                        chan.send(prompt)

                    elif char in ('\x08', '\x7f'): # Backspace
                        if len(cmd_buffer) > 0:
                            cmd_buffer = cmd_buffer[:-1]
                            chan.send('\b \b')
                    else:
                        cmd_buffer += char
                        chan.send(char)
            except Exception as e:
                logger.error(f"Error in SSH shell loop: {e}")
                break

        chan.close()

    def handle_client_connection(self, client_socket: socket.socket, addr: tuple):
        client_ip, client_port = addr
        logger.info(f"Accepted incoming SSH TCP connection from {client_ip}:{client_port}")

        transport = paramiko.Transport(client_socket)
        transport.add_server_key(self.host_key)

        server_handler = DadiwooSSHServerInterface(client_ip, client_port)
        session_id = str(uuid.uuid4())[:8]

        try:
            transport.start_server(server=server_handler)
        except paramiko.SSHException as e:
            logger.warning(f"SSH negotiation failed with {client_ip}: {e}")
            return

        channel = transport.accept(20)
        if channel is None:
            logger.info(f"No SSH channel requested by {client_ip}")
            return

        server_handler.event.wait(10)
        if not server_handler.event.is_set():
            logger.info(f"No SSH shell request received from {client_ip}")
            return

        if server_handler.authenticated_user:
            user = server_handler.authenticated_user
            conn = database.get_db_connection()
            conn.execute("""
                INSERT INTO ssh_sessions (session_id, client_ip, client_port, username, auth_method, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (session_id, client_ip, client_port, user["username"], server_handler.auth_method))
            conn.commit()
            conn.close()

            self.execute_command_shell(channel, user, client_ip, session_id)

            # Close Session
            conn = database.get_db_connection()
            conn.execute("UPDATE ssh_sessions SET status = 'closed' WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.is_running = True
            logger.info(f"SSH Server listening on TCP {self.host}:{self.port}")

            def accept_loop():
                while self.is_running:
                    try:
                        client, addr = self.server_socket.accept()
                        t = threading.Thread(target=self.handle_client_connection, args=(client, addr), daemon=True)
                        t.start()
                    except Exception:
                        if not self.is_running:
                            break

            self.thread = threading.Thread(target=accept_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            logger.warning(f"Could not bind SSH server on TCP port {self.port}: {e}")

    def stop_server(self):
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

ssh_server_instance = SSHServer()
