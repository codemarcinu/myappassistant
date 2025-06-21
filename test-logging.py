#!/usr/bin/env python3
"""
Skrypt testowy do sprawdzenia logowania FoodSave AI
"""

import json
import time

import requests


def test_backend_logs():
    """Test logów backend"""
    print("🔧 Testowanie logów backend...")

    try:
        # Test pobierania logów
        response = requests.get("http://localhost:8000/api/v1/logs?lines=10")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend logs: {len(data['logs'])} linii")
            for log in data["logs"][-3:]:  # Ostatnie 3 linie
                print(f"   {log.strip()}")
        else:
            print(f"❌ Błąd pobierania logów backend: {response.status_code}")

    except Exception as e:
        print(f"❌ Błąd połączenia z backend: {e}")


def test_frontend_logs():
    """Test logów frontend"""
    print("\n🌐 Testowanie logów frontend...")

    try:
        # Test pobierania logów frontend
        response = requests.get("http://localhost:8000/api/v1/logs/frontend?lines=10")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Frontend logs: {len(data['logs'])} linii")
            for log in data["logs"][-3:]:  # Ostatnie 3 linie
                print(f"   {log.strip()}")
        else:
            print(f"❌ Błąd pobierania logów frontend: {response.status_code}")

    except Exception as e:
        print(f"❌ Błąd połączenia z frontend: {e}")


def test_health_endpoints():
    """Test endpointów health"""
    print("\n🏥 Testowanie endpointów health...")

    endpoints = [
        ("Backend Health", "http://localhost:8000/health"),
        ("Frontend", "http://localhost:3000"),
    ]

    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: OK")
            else:
                print(f"⚠️  {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {e}")


def test_logs_monitor():
    """Test monitora logów"""
    print("\n📋 Testowanie monitora logów...")

    try:
        response = requests.get("http://localhost:8000/logs-monitor.html")
        if response.status_code == 200:
            print("✅ Monitor logów: Dostępny")
            print("   Otwórz w przeglądarce: http://localhost:8000/logs-monitor.html")
        else:
            print(f"❌ Monitor logów: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Monitor logów: {e}")


def generate_test_logs():
    """Generuje testowe logi"""
    print("\n📝 Generowanie testowych logów...")

    try:
        # Generuj różne typy logów przez API
        test_requests = [
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("GET", "/api/v1/status"),
            ("POST", "/api/v1/long-task"),
        ]

        for method, endpoint in test_requests:
            try:
                if method == "GET":
                    response = requests.get(f"http://localhost:8000{endpoint}")
                else:
                    response = requests.post(f"http://localhost:8000{endpoint}")

                print(f"   {method} {endpoint}: {response.status_code}")
                time.sleep(0.5)  # Krótka przerwa

            except Exception as e:
                print(f"   {method} {endpoint}: Błąd - {e}")

    except Exception as e:
        print(f"❌ Błąd generowania testowych logów: {e}")


def main():
    """Główna funkcja testowa"""
    print("🚀 FoodSave AI - Test Logowania")
    print("=" * 40)

    # Test endpointów health
    test_health_endpoints()

    # Generuj testowe logi
    generate_test_logs()

    # Test logów backend
    test_backend_logs()

    # Test logów frontend
    test_frontend_logs()

    # Test monitora logów
    test_logs_monitor()

    print("\n" + "=" * 40)
    print("✅ Test zakończony!")
    print("\n📋 Dostępne linki:")
    print("   🌐 Frontend: http://localhost:3000")
    print("   🔧 Backend API: http://localhost:8000")
    print("   📊 API Docs: http://localhost:8000/docs")
    print("   📋 Monitor Logów: http://localhost:8000/logs-monitor.html")


if __name__ == "__main__":
    main()
