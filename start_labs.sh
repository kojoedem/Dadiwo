#!/usr/bin/env bash
# Cyber Range Platform Start Script (Direct Host Execution)

set -e

echo "🚀 Starting Cyber Range Microservices Platform with distinct individual port allocations..."

# Sync /etc/hosts domain mappings if running with sudo/permissions
PYTHONPATH=dns python3 -c "import mini_dns; mini_dns.sync_etc_hosts()" 2>/dev/null || true

# Read dynamic configured ports, difficulty, and purpose from SQLite database if available
DB_PATH="manager.db"

get_svc_info() {
    local svc_id=$1
    local default_port=$2
    if [ -f "$DB_PATH" ]; then
        python3 -c "
import sqlite3
try:
    conn=sqlite3.connect('$DB_PATH')
    r=conn.cursor().execute(\"SELECT configured_port, difficulty, environment_purpose FROM microservices WHERE id='$svc_id'\").fetchone()
    if r:
        print(f\"{r[0]} {r[1]} {r[2]}\")
    else:
        print(\"$default_port beginner cybersecurity\")
    conn.close()
except Exception:
    print(\"$default_port beginner cybersecurity\")
" 2>/dev/null || echo "$default_port beginner cybersecurity"
    else
        echo "$default_port beginner cybersecurity"
    fi
}

read ATM_PORT ATM_DIFF ATM_PURPOSE <<< $(get_svc_info "atm" 8080)
read BANK_PORT BANK_DIFF BANK_PURPOSE <<< $(get_svc_info "bank" 8081)
read ISP_PORT ISP_DIFF ISP_PURPOSE <<< $(get_svc_info "isp" 8082)
read SCHOOL_PORT SCHOOL_DIFF SCHOOL_PURPOSE <<< $(get_svc_info "school" 8083)
read SHOP_PORT SHOP_DIFF SHOP_PURPOSE <<< $(get_svc_info "shop" 8084)
read MOBILE_PORT MOBILE_DIFF MOBILE_PURPOSE <<< $(get_svc_info "mobile" 8085)
read WAVE_PORT WAVE_DIFF WAVE_PURPOSE <<< $(get_svc_info "wave" 8086)
read SNMP_PORT SNMP_DIFF SNMP_PURPOSE <<< $(get_svc_info "snmp" 8087)
read SSH_PORT SSH_DIFF SSH_PURPOSE <<< $(get_svc_info "ssh" 8088)
read APIWAREHOUSE_PORT APIWAREHOUSE_DIFF APIWAREHOUSE_PURPOSE <<< $(get_svc_info "apiwarehouse" 8089)
read IPV6SHARK_PORT IPV6SHARK_DIFF IPV6SHARK_PURPOSE <<< $(get_svc_info "ipv6shark" 8090)

# Kill any previous uvicorn/mini_dns instances on lab ports
fuser -k 9000/tcp "${ATM_PORT}/tcp" "${BANK_PORT}/tcp" "${ISP_PORT}/tcp" "${SCHOOL_PORT}/tcp" "${SHOP_PORT}/tcp" "${MOBILE_PORT}/tcp" "${WAVE_PORT}/tcp" "${SNMP_PORT}/tcp" "${SSH_PORT}/tcp" "${APIWAREHOUSE_PORT}/tcp" "${IPV6SHARK_PORT}/tcp" 5353/udp 2222/tcp 16161/udp 2>/dev/null || true

echo "Starting Range Manager Dashboard & Mini DNS Control Plane (Port 9000)..."
PYTHONPATH=manager/app:dns python3 -m uvicorn main:app --host 0.0.0.0 --port 9000 --app-dir manager/app > /tmp/manager.log 2>&1 &

echo "Starting 🏧 ATM Lab (Port ${ATM_PORT}, Level: ${ATM_DIFF})..."
DIFFICULTY_LEVEL="${ATM_DIFF}" ENVIRONMENT_PURPOSE="${ATM_PURPOSE}" PYTHONPATH=labs/atm/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${ATM_PORT} --app-dir labs/atm/app > /tmp/atm.log 2>&1 &

echo "Starting 🏦 Bank Lab (Port ${BANK_PORT}, Level: ${BANK_DIFF})..."
DIFFICULTY_LEVEL="${BANK_DIFF}" ENVIRONMENT_PURPOSE="${BANK_PURPOSE}" PYTHONPATH=labs/bank/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${BANK_PORT} --app-dir labs/bank/app > /tmp/bank.log 2>&1 &

echo "Starting 🌐 ISP Lab (Port ${ISP_PORT}, Level: ${ISP_DIFF})..."
DIFFICULTY_LEVEL="${ISP_DIFF}" ENVIRONMENT_PURPOSE="${ISP_PURPOSE}" PYTHONPATH=labs/isp/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${ISP_PORT} --app-dir labs/isp/app > /tmp/isp.log 2>&1 &

echo "Starting 🎓 School Lab (Port ${SCHOOL_PORT}, Level: ${SCHOOL_DIFF})..."
DIFFICULTY_LEVEL="${SCHOOL_DIFF}" ENVIRONMENT_PURPOSE="${SCHOOL_PURPOSE}" PYTHONPATH=labs/school/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${SCHOOL_PORT} --app-dir labs/school/app > /tmp/school.log 2>&1 &

echo "Starting 🛒 Shop Lab (Port ${SHOP_PORT}, Level: ${SHOP_DIFF})..."
DIFFICULTY_LEVEL="${SHOP_DIFF}" ENVIRONMENT_PURPOSE="${SHOP_PURPOSE}" PYTHONPATH=labs/shop/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${SHOP_PORT} --app-dir labs/shop/app > /tmp/shop.log 2>&1 &

echo "Starting 📱 Mobile Lab (Port ${MOBILE_PORT}, Level: ${MOBILE_DIFF})..."
DIFFICULTY_LEVEL="${MOBILE_DIFF}" ENVIRONMENT_PURPOSE="${MOBILE_PURPOSE}" PYTHONPATH=labs/mobile/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${MOBILE_PORT} --app-dir labs/mobile/app > /tmp/mobile.log 2>&1 &

echo "Starting 🌊 Wave Chat Lab (Port ${WAVE_PORT}, Level: ${WAVE_DIFF})..."
DIFFICULTY_LEVEL="${WAVE_DIFF}" ENVIRONMENT_PURPOSE="${WAVE_PURPOSE}" PYTHONPATH=labs/wave/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${WAVE_PORT} --app-dir labs/wave/app > /tmp/wave.log 2>&1 &

echo "Starting 📡 SNMP Lab (Port ${SNMP_PORT}, Level: ${SNMP_DIFF})..."
DIFFICULTY_LEVEL="${SNMP_DIFF}" ENVIRONMENT_PURPOSE="${SNMP_PURPOSE}" PYTHONPATH=labs/snmp/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${SNMP_PORT} --app-dir labs/snmp/app > /tmp/snmp.log 2>&1 &

echo "Starting 🔑 SSH Lab (Port ${SSH_PORT}, Level: ${SSH_DIFF})..."
DIFFICULTY_LEVEL="${SSH_DIFF}" ENVIRONMENT_PURPOSE="${SSH_PURPOSE}" PYTHONPATH=labs/ssh/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${SSH_PORT} --app-dir labs/ssh/app > /tmp/ssh.log 2>&1 &

echo "Starting 🏬 API Warehouse Lab (Port ${APIWAREHOUSE_PORT}, Level: ${APIWAREHOUSE_DIFF})..."
DIFFICULTY_LEVEL="${APIWAREHOUSE_DIFF}" ENVIRONMENT_PURPOSE="${APIWAREHOUSE_PURPOSE}" PYTHONPATH=labs/apiwarehouse/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${APIWAREHOUSE_PORT} --app-dir labs/apiwarehouse/app > /tmp/apiwarehouse.log 2>&1 &

echo "Starting 🦈 IPv6 Shark Lab (Port ${IPV6SHARK_PORT}, Level: ${IPV6SHARK_DIFF})..."
DIFFICULTY_LEVEL="${IPV6SHARK_DIFF}" ENVIRONMENT_PURPOSE="${IPV6SHARK_PURPOSE}" PYTHONPATH=labs/ipv6shark/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${IPV6SHARK_PORT} --app-dir labs/ipv6shark/app > /tmp/ipv6shark.log 2>&1 &

sleep 2

echo "✅ All microservices started successfully on unique individual ports!"
echo "-------------------------------------------------------"
echo "🛡 Manager Dashboard: http://localhost:9000 (or http://<IP>:9000)"
echo "🌐 Mini DNS Server:  UDP Port 5353 (Configurable in Manager)"
echo "🏧 ATM Lab:          http://localhost:${ATM_PORT} (or http://atm.lab:${ATM_PORT})"
echo "🏦 Bank Lab:         http://localhost:${BANK_PORT} (or http://bank.lab:${BANK_PORT})"
echo "🌐 ISP Lab:          http://localhost:${ISP_PORT} (or http://isp.lab:${ISP_PORT})"
echo "🎓 School Lab:       http://localhost:${SCHOOL_PORT} (or http://school.lab:${SCHOOL_PORT})"
echo "🛒 Shop Lab:         http://localhost:${SHOP_PORT} (or http://shop.lab:${SHOP_PORT})"
echo "📱 Mobile Lab:       http://localhost:${MOBILE_PORT} (or http://mobile.lab:${MOBILE_PORT})"
echo "🌊 Wave Chat Lab:    http://localhost:${WAVE_PORT} (or http://wave.lab:${WAVE_PORT})"
echo "📡 SNMP Lab:         http://localhost:${SNMP_PORT} (or http://snmp.lab:${SNMP_PORT})"
echo "🔑 SSH Lab:          http://localhost:${SSH_PORT} (or http://ssh.lab:${SSH_PORT})"
echo "🏬 API Warehouse Lab: http://localhost:${APIWAREHOUSE_PORT} (or http://apiwarehouse.lab:${APIWAREHOUSE_PORT})"
echo "🦈 IPv6 Shark Lab:     http://localhost:${IPV6SHARK_PORT} (or http://ipv6.lab:${IPV6SHARK_PORT} / http://[::1]:${IPV6SHARK_PORT})"
echo "-------------------------------------------------------"
