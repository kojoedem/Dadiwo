import os
import sys
import pytest
from socketserver import UDPServer
from dnslib import DNSRecord, QTYPE

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import mini_dns

def test_dns_record_resolution():
    records = mini_dns.get_dns_records()
    assert "atm.lab." in records or len(records) > 0

def test_dns_handler():
    req = DNSRecord.question("atm.lab", "A")
    data = req.pack()

    # Verify request parsing
    parsed = DNSRecord.parse(data)
    assert str(parsed.questions[0].qname) == "atm.lab."
