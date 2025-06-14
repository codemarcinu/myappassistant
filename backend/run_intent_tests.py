import asyncio
from backend.tests.test_intent_recognition import run_tests

if __name__ == "__main__":
    print("Uruchamiam testy rozpoznawania intencji...")
    asyncio.run(run_tests()) 