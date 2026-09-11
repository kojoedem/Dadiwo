#!/usr/bin/env bash
# Cyber Range Platform Start Script (Direct Host Execution)

set -e

echo "🚀 Starting Cyber Range Microservices Platform on host..."

# Kill any previous uvicorn/mini_dns instances on lab ports
fuser -k 9000/tcp 8080/tcp 8081/tcp 8082/tcp 8083/tcp 8084/tcp 5353/udp 2>/dev/null || true

echo "Starting Range Manager Dashboard & Mini DNS Control Plane (Port 9000)..."
PYTHONPATH=manager/app:dns python3 -m uvicorn main:app --host 0.0.0.0 --port 9000 --app-dir manager/app > /tmp/manager.log 2>&1 &

echo "Starting 🏧 ATM Lab (Port 8080)..."
PYTHONPATH=labs/atm/app python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir labs/atm/app > /tmp/atm.log 2>&1 &

echo "Starting 🏦 Bank Lab (Port 8081)..."
PYTHONPATH=labs/bank/app python3 -m uvicorn main:app --host 0.0.0.0 --port 8081 --app-dir labs/bank/app > /tmp/bank.log 2>&1 &

echo "Starting 🌐 ISP Lab (Port 8082)..."
PYTHONPATH=labs/isp/app python3 -m uvicorn main:app --host 0.0.0.0 --port 8082 --app-dir labs/isp/app > /tmp/isp.log 2>&1 &

echo "Starting 🎓 School Lab (Port 8083)..."
PYTHONPATH=labs/school/app python3 -m uvicorn main:app --host 0.0.0.0 --port 8083 --app-dir labs/school/app > /tmp/school.log 2>&1 &

echo "Starting 🛒 Shop Lab (Port 8084)..."
PYTHONPATH=labs/shop/app python3 -m uvicorn main:app --host 0.0.0.0 --port 8084 --app-dir labs/shop/app > /tmp/shop.log 2>&1 &

sleep 2

echo "✅ All microservices started successfully!"
echo "-------------------------------------------------------"
echo "🛡 Manager Dashboard: http://localhost:9000 (or http://<IP>:9000)"
echo "🌐 Mini DNS Server:  UDP Port 5353 (Configurable in Manager)"
echo "🏧 ATM Lab:          http://localhost:8080 (or http://atm.lab:8080)"
echo "🏦 Bank Lab:         http://localhost:8081 (or http://bank.lab:8081)"
echo "🌐 ISP Lab:          http://localhost:8082 (or http://isp.lab:8082)"
echo "🎓 School Lab:       http://localhost:8083 (or http://school.lab:8083)"
echo "🛒 Shop Lab:         http://localhost:8084 (or http://shop.lab:8084)"
echo "-------------------------------------------------------"
