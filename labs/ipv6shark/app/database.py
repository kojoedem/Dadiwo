import sqlite3
import os

DB_PATH = os.environ.get("IPV6SHARK_DB_PATH", "ipv6shark.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            summary TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_type TEXT NOT NULL, -- 'red_team' or 'blue_team'
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            attack_vector TEXT NOT NULL,
            description TEXT NOT NULL,
            command_example TEXT NOT NULL,
            defense_mitigation TEXT NOT NULL,
            difficulty TEXT NOT NULL DEFAULT 'beginner'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ndp_neighbors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ipv6_address TEXT NOT NULL UNIQUE,
            mac_address TEXT NOT NULL,
            interface TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'REACHABLE'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            client_ip TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL
        )
    """)

    # Seed initial blog posts
    cursor.execute("SELECT COUNT(*) as count FROM blog_posts")
    if cursor.fetchone()["count"] == 0:
        posts = [
            (
                "Welcome to IPv6 Shark - Mastering IPv6 Security & Dual-Stack Hacking",
                "IPv6 Security",
                "Why IPv6 security matters and why legacy IPv4 mindsets leave production networks exposed.",
                "IPv6 is no longer just the future—it is active across almost every modern operating system and cloud environment by default. Many enterprise networks run dual-stack setups without strict IPv6 firewalls or monitoring, creating hidden attack vectors. IPv6 Shark is a dedicated microservice built for security engineers and red/blue teams to simulate, audit, and defend IPv6 deployments.",
                "IPv6 Shark Team"
            ),
            (
                "Demystifying SLAAC & Rogue Router Advertisements",
                "Red Team Attacks",
                "How an unauthorized node can send rogue IPv6 RAs to hijack network gateways and force traffic redirection.",
                "Stateless Address Autoconfiguration (SLAAC) allows IPv6 hosts to self-assign addresses based on ICMPv6 Router Advertisements (Type 134). An attacker on the local link can send rogue RAs claiming higher router priority or fake default routes, causing target hosts to route all traffic through the attacker's machine. Blue teams defend against this using Router Advertisement Guard (RA Guard) and SEND (RFC 3971).",
                "IPv6 Shark Team"
            ),
            (
                "NDP Spoofing vs ARP Poisoning: What Blue Teams Must Know",
                "Blue Team Defense",
                "Comparing IPv4 ARP spoofing with ICMPv6 Neighbor Discovery Protocol (NDP) poisoning attacks.",
                "In IPv4 networks, ARP maps IP addresses to MAC addresses. In IPv6, Neighbor Discovery Protocol (NDP) uses Neighbor Solicitation (Type 135) and Neighbor Advertisement (Type 136) ICMPv6 packets. Without Secure Neighbor Discovery (SEND) or NDP Inspection, attackers can forge Neighbor Advertisements to overwrite NDP tables and perform Man-in-the-Middle (MITM) interception.",
                "IPv6 Shark Team"
            )
        ]
        cursor.executemany("""
            INSERT INTO blog_posts (title, category, summary, content, author)
            VALUES (?, ?, ?, ?, ?)
        """, posts)

    # Seed initial scenarios
    cursor.execute("SELECT COUNT(*) as count FROM scenarios")
    if cursor.fetchone()["count"] == 0:
        scenarios = [
            (
                "red_team",
                "Rogue SLAAC Router Advertisement Injection",
                "SLAAC / ICMPv6 Type 134",
                "Rogue RA Injection (RFC 6104)",
                "Attacker broadcasts fake ICMPv6 Router Advertisements with high router preference and custom DNS servers to hijack gateway routes for all SLAAC clients.",
                "atk6-fake_router6 eth0 -A 2001:db8:cyber:1::/64 -D 2001:db8:cyber:1::53 -s fe80::bad:cafe",
                "Enable RA Guard (RFC 6105) on switch access ports to drop unauthorized Router Advertisement packets from untrusted interfaces.",
                "beginner"
            ),
            (
                "red_team",
                "NDP Poisoning & Cache Overwrite (IPv6 MITM)",
                "NDP / ICMPv6 Type 136",
                "Neighbor Advertisement Spoofing",
                "Attacker floods unsolicited Neighbor Advertisements with the target IPv6 address and attacker MAC address to redirect IPv6 traffic.",
                "atk6-parasite6 eth0 -t fe80::1001 -g fe80::1",
                "Implement Secure Neighbor Discovery (SEND - RFC 3971) with RSA signatures or dynamic IPv6 First-Hop Security (FHS) NDP inspection on managed switches.",
                "intermediate"
            ),
            (
                "red_team",
                "IPv6 Extension Header Firewall Bypass",
                "IPv6 Extension Headers",
                "Fragmentation & Hop-by-Hop Headers",
                "Attacker chains multiple IPv6 Extension Headers (Hop-by-Hop, Routing, Fragment) to obfuscate Layer 4 TCP/UDP port data from legacy stateless firewalls.",
                "nmap -6 --ip-frag 8 -sS -p 22,80,8090 2001:db8:cyber:1::100",
                "Deploy deep packet inspection (DPI) firewalls with strict IPv6 Extension Header limits (RFC 7112) and drop invalid or overlapping fragments.",
                "advanced"
            ),
            (
                "red_team",
                "IPv6 All-Nodes Multicast Reconnaissance",
                "ICMPv6 Multicast",
                "Ping6 Multicast Discovery",
                "Attacker pings link-local all-nodes multicast address ff02::1 to discover all active IPv6 hosts on the local network segment without port scanning.",
                "ping6 -I eth0 ff02::1",
                "Restrict ICMPv6 Echo Request responses on end-host firewalls (ip6tables) and monitor all-nodes multicast traffic for anomalies.",
                "beginner"
            ),
            (
                "blue_team",
                "IPv6 Router Advertisement Guard (RA Guard) Policy",
                "First-Hop Security",
                "RA Guard Deployment",
                "Configuring Layer 2 switch policy to inspect ICMPv6 Router Advertisements and block them on user-facing access ports.",
                "ipv6 nd raguard attach-policy RA_GUARD_POLICY (interface range Gi0/1 - 24)",
                "Ensures only verified router uplink ports can send ICMPv6 Type 134 packets, blocking internal SLAAC hijacking.",
                "beginner"
            ),
            (
                "blue_team",
                "Dual-Stack ip6tables Perimeter Firewall Rules",
                "Network Defense",
                "ip6tables Inbound Filtering",
                "Hardening Linux server perimeter with ip6tables to drop incoming unneeded IPv6 services while allowing essential ICMPv6 NDP packets.",
                "ip6tables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT\nip6tables -A INPUT -p icmpv6 --icmpv6-type neighbor-solicitation -j ACCEPT\nip6tables -A INPUT -p icmpv6 --icmpv6-type neighbor-advertisement -j ACCEPT\nip6tables -A INPUT -p tcp --dport 8090 -j ACCEPT\nip6tables -P INPUT DROP",
                "Prevents dual-stack perimeter bypass where IPv4 is heavily filtered but IPv6 ports remain open and exposed.",
                "intermediate"
            ),
            (
                "blue_team",
                "IPv6 Bogon Address Filtering & Monitoring",
                "Ingress / Egress Defense",
                "IPv6 Bogon ACLs",
                "Filtering unallocated or reserved IPv6 prefix ranges (0000::/8, 0100::/8, 0200::/7, 3ff2::/12, etc.) at edge routers.",
                "ipv6 access-list BOGON_FILTER deny ipv6 3ff2::/12 any\nip6tables -A INPUT -s ::/128 -j DROP",
                "Blocks spoofed or invalid IPv6 source address ranges from entering or leaving the enterprise autonomous system.",
                "advanced"
            )
        ]
        cursor.executemany("""
            INSERT INTO scenarios (scenario_type, title, category, attack_vector, description, command_example, defense_mitigation, difficulty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, scenarios)

    # Seed initial NDP neighbors
    cursor.execute("SELECT COUNT(*) as count FROM ndp_neighbors")
    if cursor.fetchone()["count"] == 0:
        neighbors = [
            ("fe80::1", "00:11:22:33:44:01", "eth0", "REACHABLE"),
            ("fe80::1001", "00:11:22:33:44:02", "eth0", "STALE"),
            ("2001:db8:cyber:1::1", "52:54:00:12:34:56", "eth0", "REACHABLE"),
            ("2001:db8:cyber:1::8090", "02:42:ac:11:00:02", "eth0", "PERMANENT")
        ]
        cursor.executemany("""
            INSERT INTO ndp_neighbors (ipv6_address, mac_address, interface, state)
            VALUES (?, ?, ?, ?)
        """, neighbors)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
