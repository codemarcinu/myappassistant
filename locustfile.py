import json
import random
import time

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner


class FoodSaveAIUser(HttpUser):
    """
    Load test user dla FoodSave AI Backend
    Symuluje rzeczywiste zachowania użytkowników
    """

    wait_time = between(2, 5)  # Realistic user behavior

    def on_start(self):
        """Inicjalizacja użytkownika"""
        self.session_id = f"load_test_user_{random.randint(1000, 9999)}"
        self.test_queries = [
            "Jakie przepisy mogę przygotować z jajek i mąki?",
            "Dodaj jabłka do listy zakupów",
            "Jaka jest pogoda w Warszawie?",
            "Znajdź przepis na pizzę",
            "Zaplanuj posiłki na tydzień",
            "Przetwórz paragon z zakupów",
            "Pokaż mi moją spiżarnię",
            "Znajdź informacje o zdrowym odżywianiu",
        ]

    @task(4)  # Najczęstszy - chat queries
    def chat_query(self):
        """Test głównego endpointu chat"""
        query = random.choice(self.test_queries)
        payload = {"session_id": self.session_id, "query": query}

        with self.client.post(
            "/process_query", json=payload, catch_response=True, name="Chat Query"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success") or "response" in data:
                        response.success()
                    else:
                        response.failure(f"Invalid response format: {data}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)  # OCR processing
    def ocr_processing(self):
        """Test OCR endpointu"""
        # Symulacja uploadu obrazu (base64 encoded minimal image)
        test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

        payload = {
            "session_id": self.session_id,
            "file_data": test_image,
            "file_type": "image",
        }

        with self.client.post(
            "/api/v2/receipts/process",
            json=payload,
            catch_response=True,
            name="OCR Processing",
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"OCR failed: {response.status_code}")

    @task(1)  # RAG operations
    def rag_query(self):
        """Test RAG endpointu"""
        rag_queries = [
            "Jak przechowywać żywność?",
            "Zasady zdrowego odżywiania",
            "Przepisy na szybkie dania",
        ]

        payload = {"query": random.choice(rag_queries), "session_id": self.session_id}

        with self.client.post(
            "/api/v2/rag/query", json=payload, catch_response=True, name="RAG Query"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"RAG failed: {response.status_code}")

    @task(1)  # Weather queries
    def weather_query(self):
        """Test weather endpointu"""
        cities = ["Warszawa", "Kraków", "Gdańsk", "Wrocław", "Poznań"]

        payload = {
            "session_id": self.session_id,
            "query": f"Jaka jest pogoda w {random.choice(cities)}?",
        }

        with self.client.post(
            "/process_query", json=payload, catch_response=True, name="Weather Query"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Weather failed: {response.status_code}")

    @task(1)  # Health checks
    def health_check(self):
        """Test health check endpointów"""
        endpoints = ["/health", "/ready", "/api/v1/status"]

        for endpoint in endpoints:
            with self.client.get(
                endpoint, catch_response=True, name=f"Health Check - {endpoint}"
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Health check failed: {response.status_code}")

    @task(1)  # Metrics endpoint
    def metrics_check(self):
        """Test metrics endpointu"""
        with self.client.get(
            "/metrics", catch_response=True, name="Metrics Endpoint"
        ) as response:
            if response.status_code == 200 and "prometheus" in response.text.lower():
                response.success()
            else:
                response.failure(f"Metrics failed: {response.status_code}")


class MemoryIntensiveUser(HttpUser):
    """
    Użytkownik testujący memory-intensive operations
    """

    wait_time = between(5, 10)

    def on_start(self):
        self.session_id = f"memory_test_user_{random.randint(1000, 9999)}"

    @task(1)
    def bulk_operations(self):
        """Test bulk operations - memory intensive"""
        # Symulacja wielu równoczesnych zapytań
        queries = [
            "Przetwórz dużą listę produktów",
            "Znajdź wszystkie przepisy z kurczakiem",
            "Zaplanuj menu na miesiąc",
            "Przeanalizuj wszystkie paragony z ostatniego roku",
        ]

        for query in queries:
            payload = {"session_id": self.session_id, "query": query}

            with self.client.post(
                "/process_query",
                json=payload,
                catch_response=True,
                name="Bulk Operations",
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Bulk operation failed: {response.status_code}")


# Event handlers dla monitoring
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Inicjalizacja load test"""
    print("🚀 FoodSave AI Load Test Started")
    print(f"Target: {environment.host}")
    print("Test scenarios:")
    print("- Chat queries (40% load)")
    print("- OCR processing (20% load)")
    print("- RAG operations (10% load)")
    print("- Weather queries (10% load)")
    print("- Health checks (10% load)")
    print("- Metrics endpoint (10% load)")
    print("- Memory intensive operations (separate user class)")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Test started event"""
    print("📊 Load test started - monitoring performance...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Test stopped event"""
    print("✅ Load test completed")
    print("📈 Check results in Locust web interface")


# Custom metrics collection
@events.request.add_listener
def on_request(
    request_type,
    name,
    response_time,
    response_length,
    response,
    context,
    exception,
    start_time,
    url,
    **kwargs,
):
    """Custom request monitoring"""
    if exception:
        print(f"❌ Request failed: {name} - {exception}")
    elif response_time > 5000:  # 5 seconds threshold
        print(f"⚠️  Slow request: {name} - {response_time}ms")
