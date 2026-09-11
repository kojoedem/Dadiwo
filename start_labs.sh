#!/usr/bin/env bash
# Cyber Range Platform Start Script (Direct Host Execution)

set -e

echo "🚀 Starting Cyber Range Microservices Platform with distinct individual port allocations..."

# Sync /etc/hosts domain mappings if running with sudo/permissions
PYTHONPATH=dns python3 -c "import mini_dns; mini_dns.sync_etc_hosts()" 2>/dev/null || true

# Read dynamic configured ports from SQLite database if available
DB_PATH="manager.db"
if [ -f "$DB_PATH" ]; then
    ATM_PORT=$(python3 -c "import sqlite3; conn=sqlite3.connect('$DB_PATH'); cursor=conn.cursor(); r=cursor.execute(\"SELECT configured_port FROM microservices WHERE id='atm'\").fetchone(); print(r[0] if r else 8080); conn.close()" 2>/dev/null || echo 8080)
    BANK_PORT=$(python3 -c "import sqlite3; conn=sqlite3.connect('$DB_PATH'); cursor=conn.cursor(); r=cursor.execute(\"SELECT configured_port FROM microservices WHERE id='bank'\").fetchone(); print(r[0] if r else 8081); conn.close()" 2>/dev/null || echo 8081)
    ISP_PORT=$(python3 -c "import sqlite3; conn=sqlite3.connect('$DB_PATH'); cursor=conn.cursor(); r=cursor.execute(\"SELECT configured_port FROM microservices WHERE id='isp'\").fetchone(); print(r[0] if r else 8082); conn.close()" 2>/dev/null || echo 8082)
    SCHOOL_PORT=$(python3 -c "import sqlite3; conn=sqlite3.connect('$DB_PATH'); cursor=conn.cursor(); r=cursor.execute(\"SELECT configured_port FROM microservices WHERE id='school'\").fetchone(); print(r[0] if r else 8083); conn.close()" 2>/dev/null || echo 8083)
    SHOP_PORT=$(python3 -c "import sqlite3; conn=sqlite3.connect('$DB_PATH'); cursor=conn.cursor(); r=cursor.execute(\"SELECT configured_port FROM microservices WHERE id='shop'\").fetchone(); print(r[0] if r else 8084); conn.close()" 2>/dev/null || echo 8084)
    MOBILE_PORT=$(python3 -c "import sqlite3; conn=sqlite3.connect('$DB_PATH'); cursor=conn.cursor(); r=cursor.execute(\"SELECT configured_port FROM microservices WHERE id='mobile'\").fetchone(); print(r[0] if r else 8085); conn.close()" 2>/dev/null || echo 8085)
else
    ATM_PORT=8080
    BANK_PORT=8081
    ISP_PORT=8082
    SCHOOL_PORT=8083
    SHOP_PORT=8084
    MOBILE_PORT=8085
fi

# Kill any previous uvicorn/mini_dns instances on lab ports
fuser -k 9000/tcp "${ATM_PORT}/tcp" "${BANK_PORT}/tcp" "${ISP_PORT}/tcp" "${SCHOOL_PORT}/tcp" "${SHOP_PORT}/tcp" "${MOBILE_PORT}/tcp" 5353/udp 2>/dev/null || true

echo "Starting Range Manager Dashboard & Mini DNS Control Plane (Port 9000)..."
PYTHONPATH=manager/app:dns python3 -m uvicorn main:app --host 0.0.0.0 --port 9000 --app-dir manager/app > /tmp/manager.log 2>&1 &

echo "Starting 🏧 ATM Lab (Port ${ATM_PORT})..."
PYTHONPATH=labs/atm/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${ATM_PORT} --app-dir labs/atm/app > /tmp/atm.log 2>&1 &

echo "Starting 🏦 Bank Lab (Port ${BANK_PORT})..."
PYTHONPATH=labs/bank/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${BANK_PORT} --app-dir labs/bank/app > /tmp/bank.log 2>&1 &

echo "Starting 🌐 ISP Lab (Port ${ISP_PORT})..."
PYTHONPATH=labs/isp/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${ISP_PORT} --app-dir labs/isp/app > /tmp/isp.log 2>&1 &

echo "Starting 🎓 School Lab (Port ${SCHOOL_PORT})..."
PYTHONPATH=labs/school/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${SCHOOL_PORT} --app-dir labs/school/app > /tmp/school.log 2>&1 &

echo "Starting 🛒 Shop Lab (Port ${SHOP_PORT})..."
PYTHONPATH=labs/shop/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${SHOP_PORT} --app-dir labs/shop/app > /tmp/shop.log 2>&1 &

echo "Starting 📱 Mobile Lab (Port ${MOBILE_PORT})..."
PYTHONPATH=labs/mobile/app python3 -m uvicorn main:app --host 0.0.0.0 --port ${MOBILE_PORT} --app-dir labs/mobile/app > /tmp/mobile.log 2>&1 &

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
echo "-------------------------------------------------------"
