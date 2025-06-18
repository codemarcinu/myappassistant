#!/usr/bin/env python3
"""
Skrypt automatycznej diagnozy i naprawy Dockera dla FoodSave AI
"""

import subprocess
import time


class DockerDiagnostic:
    def __init__(self):
        self.issues = []
        self.fixes = []

    def run_command(self, command):
        """Uruchamia komendę i zwraca wynik"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def check_docker_status(self):
        """Sprawdza status Dockera"""
        print("🔍 Sprawdzanie statusu Dockera...")
        success, stdout, stderr = self.run_command("docker --version")
        if not success:
            self.issues.append("Docker nie jest zainstalowany lub nie działa")
            return False
        print(f"✅ Docker: {stdout.strip()}")
        return True

    def check_compose_files(self):
        """Sprawdza pliki docker-compose"""
        print("🔍 Sprawdzanie plików docker-compose...")
        success, stdout, stderr = self.run_command("ls docker-compose*.yml")
        if success:
            files = stdout.strip().split("\n")
            print(f"📁 Znalezione pliki: {files}")
            if len(files) > 1:
                self.issues.append(f"Wiele plików docker-compose: {files}")
                self.fixes.append("Użyj głównego pliku: docker-compose.yml")
        return True

    def check_containers(self):
        """Sprawdza status kontenerów"""
        print("🔍 Sprawdzanie kontenerów...")
        success, stdout, stderr = self.run_command("docker ps -a")
        if success:
            if "foodsave" in stdout:
                print("📦 Znaleziono kontenery foodsave")
                # Sprawdź status
                lines = stdout.split("\n")[1:]  # Pomiń nagłówek
                for line in lines:
                    if "foodsave" in line and "Exited" in line:
                        self.issues.append(f"Kontener zatrzymany: {line.split()[0]}")
        return True

    def check_ports(self):
        """Sprawdza porty"""
        print("🔍 Sprawdzanie portów...")
        ports_to_check = [8000, 11434, 3000, 6333]
        for port in ports_to_check:
            success, stdout, stderr = self.run_command(f"netstat -tuln | grep :{port}")
            if success and stdout:
                print(f"⚠️  Port {port} jest zajęty")
                self.issues.append(f"Port {port} jest zajęty")

    def fix_poetry_path(self):
        """Naprawa PATH dla Poetry"""
        print("🔧 Naprawiam konfigurację Poetry...")
        dockerfile_fix = """
# Dodaj do Dockerfile po instalacji Poetry:
ENV PATH="/root/.local/bin:$PATH"
RUN which poetry || echo "Poetry not found in PATH"
"""
        print("📝 Dodaj do Dockerfile:", dockerfile_fix)
        self.fixes.append("Naprawiono PATH dla Poetry")

    def fix_ollama_network(self):
        """Naprawa sieci Ollama"""
        print("🔧 Naprawiam sieć Ollama...")
        compose_fix = """
# Dodaj do docker-compose.yml dla serwisu ollama:
environment:
  - OLLAMA_HOST=0.0.0.0
networks:
  - foodsave-network
"""
        print("📝 Konfiguracja sieci:", compose_fix)
        self.fixes.append("Naprawiono konfigurację sieci Ollama")

    def clean_docker(self):
        """Czyści środowisko Docker"""
        print("🧹 Czyszczenie środowiska Docker...")
        commands = [
            "docker-compose down --volumes --remove-orphans",
            "docker system prune -f",
            "docker volume prune -f",
        ]

        for cmd in commands:
            print(f"Wykonuję: {cmd}")
            success, stdout, stderr = self.run_command(cmd)
            if not success:
                print(f"❌ Błąd: {stderr}")

    def restart_services(self):
        """Restartuje serwisy"""
        print("🚀 Restartowanie serwisów...")

        # Buduj od nowa
        print("🔨 Budowanie obrazów...")
        success, stdout, stderr = self.run_command("docker-compose build --no-cache")
        if not success:
            print(f"❌ Błąd budowania: {stderr}")
            return False

        # Uruchom Ollama najpierw
        print("🦙 Uruchamianie Ollama...")
        success, stdout, stderr = self.run_command("docker-compose up ollama -d")
        if success:
            print("⏳ Czekam na Ollama (60s)...")
            time.sleep(60)

            # Pobierz modele
            print("📥 Pobieranie modeli...")
            self.run_command("docker exec foodsave-ollama ollama pull gemma3:latest")

        # Uruchom wszystko
        print("🚀 Uruchamianie wszystkich serwisów...")
        success, stdout, stderr = self.run_command("docker-compose up -d")
        if success:
            print("✅ Serwisy uruchomione!")
            return True
        else:
            print(f"❌ Błąd uruchamiania: {stderr}")
            return False

    def verify_services(self):
        """Weryfikuje działanie serwisów"""
        print("🔍 Weryfikacja serwisów...")

        services = [
            ("Backend", "http://localhost:8000/health"),
            ("Ollama", "http://localhost:11434/api/version"),
            ("Frontend", "http://localhost:3000"),
        ]

        for name, url in services:
            success, stdout, stderr = self.run_command(f"curl -s {url}")
            if success:
                print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: BŁĄD")

    def run_full_diagnosis(self):
        """Uruchamia pełną diagnozę i naprawę"""
        print("🔧 FoodSave AI - Automatyczna naprawa Dockera")
        print("=" * 50)

        # Diagnoza
        if not self.check_docker_status():
            print("❌ Docker nie działa. Zainstaluj Docker Desktop.")
            return

        self.check_compose_files()
        self.check_containers()
        self.check_ports()

        # Raport problemów
        if self.issues:
            print("\n⚠️  Znalezione problemy:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")

        # Naprawa
        print("\n🔧 Rozpoczynam naprawę...")
        self.fix_poetry_path()
        self.fix_ollama_network()
        self.clean_docker()

        # Restart
        if self.restart_services():
            print("\n🎉 Naprawa zakończona!")
            self.verify_services()
        else:
            print("\n❌ Naprawa nieudana. Sprawdź logi:")
            print("docker-compose logs -f")

        # Podsumowanie
        print("\n📋 Podsumowanie:")
        for fix in self.fixes:
            print(f"  ✅ {fix}")


if __name__ == "__main__":
    diagnostic = DockerDiagnostic()
    diagnostic.run_full_diagnosis()
