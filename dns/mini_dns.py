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
    if os.path.exists(MANAGER_DB_PATH):
        try:
            conn = sqlite3.connect(MANAGER_DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Fetch global host IP from dns_settings if set
            settings = cursor.execute("SELECT host_ip FROM dns_settings LIMIT 1").fetchone()
            current_host_ip = settings["host_ip"] if settings else HOST_IP

            services = cursor.execute("SELECT local_domain FROM microservices").fetchall()
            for s in services:
                domain = s["local_domain"].strip()
                if not domain.endswith("."):
                    domain += "."
                records[domain] = current_host_ip
            conn.close()
        except Exception as e:
            print(f"[DNS] DB fetch error: {e}")

    if not records:
        records = {
            "atm.lab.": HOST_IP,
            "bank.lab.": HOST_IP,
            "isp.lab.": HOST_IP,
            "school.lab.": HOST_IP,
            "shop.lab.": HOST_IP
        }
    return records

class DNSHandler(BaseRequestHandler):
    def handle(self):
        data, sock = self.request
        records = get_dns_records()

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
                    # Fallback wildcard match if ends with .lab or .lab.local
                    if domain.endswith(".lab.") or domain.endswith(".lab.local."):
                        target_ip = list(records.values())[0] if records else HOST_IP
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
        print(f"Mini DNS server running on UDP port {self.port}")
        self.server = UDPServer((self.host, self.port), DNSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("Mini DNS server stopped.")

if __name__ == "__main__":
    print(f"Mini DNS server running on UDP port {PORT}")
    with UDPServer(("0.0.0.0", PORT), DNSHandler) as server:
        server.serve_forever()
