import asyncio

from backend.tests import test_intent_recognition

if __name__ == "__main__":
    print("Uruchamiam testy rozpoznawania intencji...")
    asyncio.run(test_intent_recognition.run_tests())
