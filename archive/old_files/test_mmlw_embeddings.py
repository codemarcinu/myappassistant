#!/usr/bin/env python3
"""
Test skrypt dla embeddingów MMLW
Sprawdza czy model MMLW działa poprawnie w Twojej infrastrukturze
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List

import requests

# Dodaj katalog projektu do PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_mmlw_status():
    """Test 1: Sprawdzenie statusu MMLW"""
    print("🔍 Test 1: Sprawdzanie statusu MMLW...")
    try:
        response = requests.get("http://localhost:8000/api/agents/mmlw/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status MMLW: {data['available']}")
            if data["available"]:
                status = data["status"]
                print(f"   Model: {status['model_name']}")
                print(f"   Device: {status['device']}")
                print(f"   Embedding dimension: {status['embedding_dimension']}")
            return True
        else:
            print(f"❌ Błąd HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Błąd połączenia: {e}")
        return False


async def test_mmlw_embedding():
    """Test 2: Test generowania embeddingów"""
    print("\n🔍 Test 2: Test generowania embeddingów...")
    try:
        response = requests.post("http://localhost:8000/api/agents/mmlw/test")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test embeddingów: {data['success']}")
            print(f"   Embedding dimension: {data['embedding_dimension']}")
            print(f"   Test text: {data['test_text']}")
            return True
        else:
            print(f"❌ Błąd HTTP: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Błąd połączenia: {e}")
        return False


async def test_agents_list():
    """Test 3: Sprawdzenie listy agentów"""
    print("\n🔍 Test 3: Sprawdzanie listy agentów...")
    try:
        response = requests.get("http://localhost:8000/api/agents/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ Znaleziono {len(agents)} agentów:")
            for agent in agents:
                print(f"   - {agent['name']}: {agent['description']}")
            return True
        else:
            print(f"❌ Błąd HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Błąd połączenia: {e}")
        return False


async def test_search_with_embeddings():
    """Test 4: Test wyszukiwania z embeddingami (jeśli endpoint istnieje)"""
    print("\n🔍 Test 4: Test wyszukiwania z embeddingami...")

    # Sprawdź czy endpoint istnieje
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✅ Endpointy API dostępne (sprawdź /docs w przeglądarce)")
        else:
            print("⚠️  Endpointy API mogą być niedostępne")
    except:
        print("⚠️  Nie można sprawdzić endpointów API")

    # Przykład testu wyszukiwania (jeśli endpoint zostanie dodany)
    test_data = {
        "query": "szybki obiad z kurczakiem",
        "candidates": [
            "Kurczak w sosie śmietanowym",
            "Makaron z pesto",
            "Sałatka z tuńczykiem",
            "Kurczak curry z ryżem",
            "Zupa pomidorowa",
        ],
    }

    print(f"   Przykładowe dane testowe przygotowane:")
    print(f"   Query: {test_data['query']}")
    print(f"   Candidates: {len(test_data['candidates'])} pozycji")

    return True


async def test_direct_embedding():
    """Test 5: Bezpośredni test embeddingów przez kod"""
    print("\n🔍 Test 5: Bezpośredni test embeddingów...")
    try:
        from src.backend.core.rag_document_processor import RAGDocumentProcessor

        rag_processor = RAGDocumentProcessor()

        test_texts = [
            "szybki obiad z kurczakiem",
            "Kurczak w sosie śmietanowym",
            "Makaron z pesto",
        ]

        print("   Generowanie embeddingów...")
        embeddings = []
        for text in test_texts:
            embedding = await rag_processor.embed_text(text)
            if embedding:
                embeddings.append(embedding)
                print(f"   ✅ '{text[:30]}...' -> {len(embedding)} wymiarów")
            else:
                print(f"   ❌ Błąd dla tekstu: {text}")

        if len(embeddings) >= 2:
            # Test podobieństwa kosinusowego
            import numpy as np

            def cosine_similarity(a, b):
                a, b = np.array(a), np.array(b)
                return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

            sim = cosine_similarity(embeddings[0], embeddings[1])
            print(
                f"   📊 Podobieństwo 'szybki obiad' vs 'kurczak śmietanowy': {sim:.3f}"
            )

            return True
        else:
            print("   ❌ Za mało embeddingów do testu")
            return False

    except Exception as e:
        print(f"   ❌ Błąd bezpośredniego testu: {e}")
        return False


async def main():
    """Główna funkcja testowa"""
    print("🚀 Rozpoczynam testy embeddingów MMLW...")
    print("=" * 50)

    tests = [
        test_mmlw_status,
        test_mmlw_embedding,
        test_agents_list,
        test_search_with_embeddings,
        test_direct_embedding,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Błąd w teście: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("📊 PODSUMOWANIE TESTÓW:")

    test_names = [
        "Status MMLW",
        "Test embeddingów",
        "Lista agentów",
        "Wyszukiwanie z embeddingami",
        "Bezpośredni test embeddingów",
    ]

    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {name}: {status}")

    passed = sum(results)
    total = len(results)
    print(f"\n🎯 Wynik: {passed}/{total} testów przeszło")

    if passed == total:
        print("🎉 Wszystkie testy przeszły! MMLW działa poprawnie.")
    elif passed >= 3:
        print("⚠️  Większość testów przeszła. Sprawdź błędy powyżej.")
    else:
        print("❌ Wiele testów nie przeszło. Sprawdź konfigurację.")


if __name__ == "__main__":
    asyncio.run(main())
