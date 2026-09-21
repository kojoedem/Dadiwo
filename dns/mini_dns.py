import sys
import os
import sqlite3
import threading
from socketserver import UDPServer, BaseRequestHandler
from dnslib import DNSRecord, RR, A, QTYPE

PORT = int(os.environ.get("DNS_PORT", 5353))
HOST_IP = os.environ.get("HOST_IP", "127.0.0.1")
MANAGER_DB_PATH = os.environ.get("MANAGER_DB_PATH", "manager.db")

def get_dns_records():
    records = {}
    current_host_ip = HOST_IP
    if os.path.exists(MANAGER_DB_PATH):
        try:
            conn = sqlite3.connect(MANAGER_DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            settings = cursor.execute("SELECT host_ip FROM dns_settings LIMIT 1").fetchone()
            if settings and settings["host_ip"]:
                current_host_ip = settings["host_ip"]

            services = cursor.execute("SELECT local_domain FROM microservices").fetchall()
            for s in services:
                domain = s["local_domain"].strip()
                if not domain.endswith("."):
                    domain += "."
                records[domain] = current_host_ip
            conn.close()
        except Exception as e:
            print(f"[DNS] DB fetch error: {e}")

    if "dadiwoo-dash.lab." not in records:
        records["dadiwoo-dash.lab."] = current_host_ip

    if not records:
        records = {
            "atm.lab.": current_host_ip,
            "bank.lab.": current_host_ip,
            "isp.lab.": current_host_ip,
            "school.lab.": current_host_ip,
            "shop.lab.": current_host_ip,
            "mobile.lab.": current_host_ip,
            "wave.lab.": current_host_ip,
            "snmp.lab.": current_host_ip,
            "ssh.lab.": current_host_ip,
            "apiwarehouse.lab.": current_host_ip,
            "dadiwoo-dash.lab.": current_host_ip
        }
    return records, current_host_ip

def generate_hosts_entry_text(host_ip=None):
    """
    Generates the exact /etc/hosts formatted string for easy copy-pasting or auto-syncing.
    """
    records, default_ip = get_dns_records()
    target_ip = host_ip or default_ip
    domains_list = [d.rstrip(".") for d in records.keys()]
    required_domains = ["atm.lab", "bank.lab", "isp.lab", "school.lab", "shop.lab", "mobile.lab", "wave.lab", "snmp.lab", "ssh.lab", "apiwarehouse.lab", "dadiwoo-dash.lab"]
    for req in required_domains:
        if req not in domains_list:
            domains_list.append(req)
    return f"{target_ip}\t" + " ".join(sorted(set(domains_list)))

def generate_hosts_command(host_ip=None):
    """
    Generates the exact command to append hosts to /etc/hosts via sudo tee on Linux / macOS.
    """
    entry_text = generate_hosts_entry_text(host_ip)
    return f'echo "{entry_text}" | sudo tee -a /etc/hosts'

def generate_windows_hosts_command(host_ip=None):
    """
    Generates PowerShell command to update C:\\Windows\\System32\\drivers\\etc\\hosts on Windows.
    """
    entry_text = generate_hosts_entry_text(host_ip)
    return f'Add-Content -Path C:\\Windows\\System32\\drivers\\etc\\hosts -Value "{entry_text}"'

def sync_etc_hosts(host_ip=None):
    """
    Attempts to update /etc/hosts with cyber range .lab domain entries if writable.
    """
    entry_line = generate_hosts_entry_text(host_ip)
    hosts_file = "/etc/hosts"
    start_marker = "# === CYBER RANGE LAB DOMAINS START ==="
    end_marker = "# === CYBER RANGE LAB DOMAINS END ==="

    try:
        content = ""
        if os.path.exists(hosts_file):
            with open(hosts_file, "r") as f:
                content = f.read()

        if start_marker in content and end_marker in content:
            before = content.split(start_marker)[0]
            after = content.split(end_marker)[1]
            new_content = before.strip() + "\n\n" + start_marker + "\n" + entry_line + "\n" + end_marker + "\n" + after.lstrip()
        else:
            new_content = content.strip() + "\n\n" + start_marker + "\n" + entry_line + "\n" + end_marker + "\n"

        with open(hosts_file, "w") as f:
            f.write(new_content)
        print(f"[+] [DNS] Successfully updated {hosts_file} with domains.")
        return True
    except Exception as e:
        import subprocess
        try:
            cmd = f'echo "{entry_line}" | sudo -n tee -a /etc/hosts'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"[+] [DNS] Successfully updated {hosts_file} via sudo tee.")
                return True
        except Exception:
            pass
        print(f"[-] [DNS] Note: Could not write directly to /etc/hosts ({e}). Please run with sudo or add this line to /etc/hosts:\n    {entry_line}")
        return False

class DNSHandler(BaseRequestHandler):
    def handle(self):
        data, sock = self.request
        records, default_ip = get_dns_records()

        try:
            request = DNSRecord.parse(data)
            reply = request.reply()

            for question in request.questions:
                domain = str(question.qname)

                if domain in records and question.qtype == QTYPE.A:
                    target_ip = records[domain]
                    reply.add_answer(
                        RR(
                            domain,
                            QTYPE.A,
                            rdata=A(target_ip),
                            ttl=60
                        )
                    )
                    print(f"[+] [DNS] Resolved {domain} -> {target_ip}")
                else:
                    if domain.endswith(".lab.") or domain.endswith(".lab.local."):
                        target_ip = list(records.values())[0] if records else default_ip
                        reply.add_answer(
                            RR(domain, QTYPE.A, rdata=A(target_ip), ttl=60)
                        )
                        print(f"[+] [DNS Wildcard] Resolved {domain} -> {target_ip}")
                    else:
                        print(f"[-] [DNS] No record for {domain}")

            sock.sendto(reply.pack(), self.client_address)

        except Exception as e:
            print(f"Error: {e}")

class MiniDNSServer:
    def __init__(self, host="0.0.0.0", port=PORT):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        sync_etc_hosts()
        print(f"Mini DNS server running on UDP port {self.port}")
        try:
            self.server = UDPServer((self.host, self.port), DNSHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
        except Exception as e:
            print(f"[-] [DNS Server Error] Could not bind to port {self.port}: {e}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("Mini DNS server stopped.")

if __name__ == "__main__":
    sync_etc_hosts()
    print(f"Mini DNS server running on UDP port {PORT}")
    with UDPServer(("0.0.0.0", PORT), DNSHandler) as server:
        server.serve_forever()
