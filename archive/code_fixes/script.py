# Analiza załączonych logów testów
with open("paste.txt", "r", encoding="utf-8") as f:
    test_logs = f.read()

# Znajdź wszystkie błędy FAILED i ERROR
import re

failed_tests = re.findall(r"FAILED ([^-]+) - (.+)", test_logs)
error_tests = re.findall(r"ERROR ([^-]+) - (.+)", test_logs)

print("=== ANALIZA BŁĘDÓW TESTÓW ===")
print(f"Liczba testów FAILED: {len(failed_tests)}")
print(f"Liczba testów ERROR: {len(error_tests)}")

print("\n=== NAJCZĘSTSZE BŁĘDY ===")
error_patterns = {}
for test, error in failed_tests + error_tests:
    # Wyodrębnienie głównego typu błędu
    if "Multiple classes found for path" in error:
        error_type = "SQLAlchemy Multiple Classes"
    elif "One or more mappers failed to initialize" in error:
        error_type = "SQLAlchemy Mapper Initialization"
    elif "Unsupported agent type" in error:
        error_type = "Unsupported Agent Type"
    elif "AttributeError" in error:
        error_type = "AttributeError"
    elif "AssertionError" in error:
        error_type = "AssertionError"
    elif "async def functions are not natively supported" in error:
        error_type = "Async Function Support"
    elif "NameError" in error:
        error_type = "NameError"
    else:
        error_type = "Other"

    error_patterns[error_type] = error_patterns.get(error_type, 0) + 1

for error_type, count in sorted(
    error_patterns.items(), key=lambda x: x[1], reverse=True
):
    print(f"{error_type}: {count} wystąpień")

print("\n=== SZCZEGÓŁOWE PRZYKŁADY BŁĘDÓW ===")
print("1. SQLAlchemy Multiple Classes:")
sqlalchemy_errors = [
    error
    for test, error in failed_tests + error_tests
    if "Multiple classes found for path" in error
]
if sqlalchemy_errors:
    print(f"   - {sqlalchemy_errors[0][:100]}...")

print("\n2. Unsupported Agent Type:")
agent_errors = [
    error
    for test, error in failed_tests + error_tests
    if "Unsupported agent type" in error
]
if agent_errors:
    print(f"   - {agent_errors[0][:100]}...")

print("\n3. AttributeError:")
attr_errors = [
    error for test, error in failed_tests + error_tests if "AttributeError" in error
]
if attr_errors:
    print(f"   - {attr_errors[0][:100]}...")
