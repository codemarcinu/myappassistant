# Przeanalizujmy konkretne błędy z logów aby zidentyfikować kluczowe problemy

with open("paste.txt", "r", encoding="utf-8", errors="ignore") as f:
    logs_content = f.read()

# Wyodrębnienie szczegółowych błędów SQLAlchemy
import re

sqlalchemy_errors = []
lines = logs_content.split("\n")

for i, line in enumerate(lines):
    if "Multiple classes found for path" in line:
        # Pobierz kontekst błędu
        context = []
        for j in range(max(0, i - 3), min(len(lines), i + 5)):
            context.append(lines[j])
        sqlalchemy_errors.append("\n".join(context))

print("=== SZCZEGÓŁOWA ANALIZA BŁĘDÓW SQLALCHEMY ===")
if sqlalchemy_errors:
    print("Przykład błędu SQLAlchemy:")
    print(sqlalchemy_errors[0][:800])
    print("...")

# Analiza błędów agent factory
agent_factory_errors = []
for i, line in enumerate(lines):
    if "Unsupported agent type" in line:
        context = []
        for j in range(max(0, i - 2), min(len(lines), i + 3)):
            context.append(lines[j])
        agent_factory_errors.append("\n".join(context))

print("\n=== SZCZEGÓŁOWA ANALIZA BŁĘDÓW AGENT FACTORY ===")
if agent_factory_errors:
    print("Przykład błędu Agent Factory:")
    print(agent_factory_errors[0][:400])

# Analiza błędów AttributeError
attribute_errors = []
for i, line in enumerate(lines):
    if "AttributeError:" in line and "object has no attribute" in line:
        attribute_errors.append(line.strip())

print("\n=== NAJCZĘSTSZE ATTRIBUTEERROR ===")
attr_counts = {}
for error in attribute_errors[:10]:  # Pierwszych 10
    # Wyodrębnij typ błędu
    match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error)
    if match:
        obj_type, attr_name = match.groups()
        key = f"{obj_type}.{attr_name}"
        attr_counts[key] = attr_counts.get(key, 0) + 1

for error_type, count in sorted(attr_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {error_type}: {count} wystąpień")

# Analiza testów async
async_errors = [
    line for line in lines if "async def functions are not natively supported" in line
]
print(f"\n=== PROBLEMY Z TESTAMI ASYNC ===")
print(f"Liczba plików z problemami async: {len(async_errors)}")

print("\n=== PODSUMOWANIE KATEGORII BŁĘDÓW ===")
categories = {
    "SQLAlchemy Multiple Classes": len(
        [l for l in lines if "Multiple classes found for path" in l]
    ),
    "SQLAlchemy Mapper Init": len(
        [l for l in lines if "One or more mappers failed to initialize" in l]
    ),
    "Agent Factory": len([l for l in lines if "Unsupported agent type" in l]),
    "AttributeError": len([l for l in lines if "AttributeError:" in l]),
    "AssertionError": len([l for l in lines if "AssertionError:" in l]),
    "Async Support": len(
        [l for l in lines if "async def functions are not natively supported" in l]
    ),
    "Import Errors": len(
        [l for l in lines if "ImportError:" in l or "ModuleNotFoundError:" in l]
    ),
}

for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    print(f"{category}: {count}")
