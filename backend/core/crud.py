import re
from datetime import date, timedelta
from typing import Optional, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from calendar import monthrange
from ..models.shopping import Product, ShoppingTrip

# Słownik do tłumaczenia polskich nazw miesięcy w dopełniaczu (np. 10 czerwca)
POLISH_MONTHS_GENITIVE = {
    'stycznia': 1, 'lutego': 2, 'marca': 3, 'kwietnia': 4, 'maja': 5, 'czerwca': 6,
    'lipca': 7, 'sierpnia': 8, 'września': 9, 'października': 10, 'listopada': 11, 'grudnia': 12
}

# NOWOŚĆ: Słownik do tłumaczenia dni tygodnia
POLISH_WEEKDAYS = {
    'poniedziałek': 0, 'wtorek': 1, 'środa': 2, 'czwartek': 3, 'piątek': 4, 'sobota': 5, 'niedziela': 6
}

# Słownik mapujący nazwy z LLM na nazwy atrybutów w modelach
FIELD_MAP = {
    "cena_jednostkowa": "unit_price",
    "ilosc": "quantity",
    "nazwa_artykulu": "name",
    "sklep": "store_name",
    "data_zakupow": "trip_date",
    "rabat": "discount",  # Dodajemy przyszłościowo, gdybyś dodał to pole do modelu
    "kwota_per_paragon": "total_amount",
    "kategoria": "category"  # New field for product category
}

def parse_human_date(date_string: str, today: Optional[date] = None) -> Optional[date]:
    """
    Tłumaczy "ludzki" opis daty na obiekt daty w Pythonie.
    WERSJA OSTATECZNA: Poprawiona i bardziej odporna.
    """
    if not date_string:
        return None

    if today is None:
        today = date.today()

    text = date_string.lower().strip()

    # Przypadek 1: Słowa relatywne (sprawdzamy zawieranie, a nie równość)
    if 'dzisiaj' in text:
        return today
    if 'wczoraj' in text:
        return today - timedelta(days=1)
    if 'przedwczoraj' in text:
        return today - timedelta(days=2)

    # Przypadek 2: Dni tygodnia
    # Usuwamy słowa "ostatni", "zeszły", "w" dla uproszczenia
    day_text = text.replace("ostatni", "").replace("zeszły", "").replace("w", "").strip()
    if day_text in POLISH_WEEKDAYS:
        target_weekday = POLISH_WEEKDAYS[day_text]
        today_weekday = today.weekday()
        days_ago = (today_weekday - target_weekday + 7) % 7
        if days_ago == 0: # Jeśli to ten sam dzień tygodnia, cofnij o 7 dni
            days_ago = 7
        return today - timedelta(days=days_ago)

    # Przypadek 3: Format "10 czerwca" (używamy re.search, aby znaleźć wzorzec w dowolnym miejscu)
    match = re.search(r'(\d{1,2})\s+([a-zżźćńółęąś]+)', text)
    if match:
        day, month_name = match.groups()
        month_num = POLISH_MONTHS_GENITIVE.get(month_name)
        if month_num:
            try:
                return date(today.year, month_num, int(day))
            except ValueError:
                return None
    
    return None

async def find_purchase_for_action(db: AsyncSession, entities: dict) -> list[ShoppingTrip]:
    """
    Wyszukuje w bazie danych paragony na podstawie "ludzkich" identyfikatorów. Zwraca listę!
    """
    paragon_query = select(ShoppingTrip)
    paragon_id_data = entities.get('paragon_identyfikator', {})

    if paragon_id_data:
        date_str = paragon_id_data.get('data')
        obliczona_data = parse_human_date(date_str)
        if obliczona_data:
            paragon_query = paragon_query.where(ShoppingTrip.trip_date == obliczona_data)
        
        if paragon_id_data.get('sklep'):
            paragon_query = paragon_query.where(ShoppingTrip.store_name.ilike(f"%{paragon_id_data['sklep']}%"))

        if paragon_id_data.get('kolejnosc') == 'ostatni':
            paragon_query = paragon_query.order_by(ShoppingTrip.id.desc()).limit(1)

    result = await db.execute(paragon_query)
    znalezione_paragony = list(result.scalars().all())
    print(f"Znaleziono {len(znalezione_paragony)} pasujących paragonów.")
    return znalezione_paragony

async def find_item_for_action(db: AsyncSession, entities: dict) -> list[Product]:
    """
    Wyszukuje w bazie danych artykuły na podstawie "ludzkich" identyfikatorów. Zwraca listę!
    """
    # Etap 1: Używamy naszej nowej funkcji do znalezienia paragonu
    znalezione_paragony = await find_purchase_for_action(db, entities)
    if not znalezione_paragony:
        # Komunikat o błędzie zostanie wypisany w find_purchase_for_action
        return []

    produkty = []
    produkt_id_data = entities.get('produkt_identyfikator', {})
    for paragon in znalezione_paragony:
        produkt_query = select(Product).where(Product.trip_id == paragon.id)
        if produkt_id_data and produkt_id_data.get('nazwa'):
            produkt_query = produkt_query.where(Product.name.ilike(f"%{produkt_id_data['nazwa']}%"))
        result = await db.execute(produkt_query)
        produkty += result.scalars().all()
    print(f"Znaleziono {len(produkty)} pasujących produktów na danym/danych paragonie.")
    return produkty

async def execute_action(db: AsyncSession, intent: str, target_object: Any, operations: list | None = None) -> bool:
    """
    Wykonuje finalną operację (UPDATE lub DELETE) na obiekcie z bazy danych.
    """
    if not target_object:
        print("Błąd wykonania akcji: Obiekt docelowy nie został znaleziony.")
        return False

    try:
        if intent in ["DELETE_ITEM", "DELETE_PURCHASE"]:
            print(f"Wykonuję operację DELETE na obiekcie: {target_object}")
            await db.delete(target_object)
            await db.commit()
            print("Operacja DELETE zakończona sukcesem.")
            return True

        elif intent in ["UPDATE_ITEM", "UPDATE_PURCHASE"]:
            if not operations:
                print("Błąd wykonania akcji: Brak zdefiniowanych operacji UPDATE.")
                return False

            print(f"Wykonuję operację UPDATE na obiekcie: {target_object}")
            all_ops_successful = True
            for op in operations:
                human_field_name = op.get('pole_do_zmiany')
                new_value = op.get('nowa_wartosc')
                
                # Używamy naszego słownika do tłumaczenia nazwy pola
                actual_field_name = FIELD_MAP.get(human_field_name)

                if not actual_field_name or not hasattr(target_object, actual_field_name):
                    print(f"Błąd: Nie można zmapować lub obiekt nie posiada pola dla '{human_field_name}'")
                    all_ops_successful = False
                    continue  # Przejdź do następnej operacji

                setattr(target_object, actual_field_name, new_value)
                print(f"Zmieniono pole '{actual_field_name}' na wartość '{new_value}'")

            if all_ops_successful:
                await db.commit()
                print("Operacja UPDATE zakończona sukcesem.")
                return True
            else:
                await db.rollback()
                print("Operacja UPDATE przerwana z powodu błędów.")
                return False

    except Exception as e:
        print(f"Wystąpił krytyczny błąd podczas zapisu do bazy: {e}")
        await db.rollback()
        return False
    
    return False

async def create_shopping_trip(db: AsyncSession, data: dict) -> ShoppingTrip:
    """
    Tworzy nowy wpis o zakupach wraz z listą produktów w jednej transakcji.
    WERSJA OSTATECZNA z mapowaniem pól.
    """
    try:
        paragon_info = data.get("paragon_info", {})
        lista_produktow = data.get("produkty", [])

        obliczona_data = parse_human_date(paragon_info.get("data", "dzisiaj"))
        kwota_calkowita = sum(p.get("cena_calkowita", 0) for p in lista_produktow)

        nowy_paragon = ShoppingTrip(
            trip_date=obliczona_data,
            store_name=paragon_info.get("sklep"),
            total_amount=kwota_calkowita
        )
        db.add(nowy_paragon)
        await db.flush()

        for produkt_data in lista_produktow:
            # Tłumaczymy klucze z JSON-a na atrybuty modelu SQLAlchemy
            kwargs_dla_produktu = {
                FIELD_MAP.get(key, key): value
                for key, value in produkt_data.items()
                if FIELD_MAP.get(key, key) in Product.__table__.columns
            }
            # Upewniamy się, że ID paragonu jest dodane
            kwargs_dla_produktu['trip_id'] = nowy_paragon.id
            
            nowy_produkt = Product(**kwargs_dla_produktu)
            db.add(nowy_produkt)
        
        await db.commit()
        await db.refresh(nowy_paragon)
        
        print(f"Sukces! Dodano nowy paragon (ID: {nowy_paragon.id}) z {len(lista_produktow)} produktami.")
        return nowy_paragon

    except Exception as e:
        print(f"Wystąpił błąd podczas tworzenia wpisu: {e}")
        await db.rollback()
        raise

async def get_summary(db: AsyncSession, query_params: dict) -> List[Any]:
    """
    Na podstawie planu zapytania z LLM, dynamicznie buduje i wykonuje
    zapytanie analityczne SQLAlchemy. WERSJA POPRAWIONA.
    """
    metryka = query_params.get("metryka")
    grupowanie = query_params.get("grupowanie", [])

    # Definiujemy, co będziemy wybierać z bazy
    selekcja = []
    
    # --- POPRAWIONA LOGIKA SUMOWANIA ---
    # Zawsze obliczamy sumę, mnożąc ilość przez cenę jednostkową
    if metryka == "suma_wydatkow":
        # Używamy coalesce, aby traktować NULL (brak ceny) jako 0
        suma_produktow = func.sum(Product.quantity * func.coalesce(Product.unit_price, 0))
        selekcja.append(suma_produktow.label("suma_wydatkow"))

    # Definiujemy, po czym grupować
    kolumny_grupujace = []
    for g in grupowanie:
        if g == "sklep":
            kolumna = ShoppingTrip.store_name
            selekcja.append(kolumna)
            kolumny_grupujace.append(kolumna)
        elif g == "kategoria":
            kolumna = Product.category
            selekcja.append(kolumna)
            kolumny_grupujace.append(kolumna)
            
    if not selekcja:
        return []

    # Budujemy zapytanie
    query = select(*selekcja).join(Product) # Zawsze łączymy z produktami
    
    for kol in kolumny_grupujace:
        query = query.group_by(kol)

    # Aplikowanie filtrów (można rozbudować o więcej opcji)
    filtry = query_params.get("filtry", [])
    for f in filtry:
        if f.get("pole") == "data" and f.get("operator") == "w_tym_miesiacu":
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today.replace(day=monthrange(today.year, today.month)[1])
            query = query.where(ShoppingTrip.trip_date.between(start_date, end_date))

    print("Wykonuję finalne zapytanie analityczne...")
    result = await db.execute(query)
    return list(result.all())

# Testowanie funkcji parse_human_date
if __name__ == '__main__':
    print("--- Testowanie parse_human_date ---")
    
    # Ustawiamy datę testową na 14 czerwca 2025 (sobota)
    test_date = date(2025, 6, 14)
    
    print(f"Test dla 'dzisiaj': {parse_human_date('dzisiaj', test_date)}")
    print(f"Test dla 'wczoraj': {parse_human_date('wczoraj', test_date)}")
    print(f"Test dla 'w piątek': {parse_human_date('w piątek', test_date)}") # Oczekiwano: 2025-06-13
    print(f"Test dla 'w ostatni poniedziałek': {parse_human_date('w ostatni poniedziałek', test_date)}") # Oczekiwano: 2025-06-09
    print(f"Test dla 'sobota': {parse_human_date('sobota', test_date)}") # Oczekiwano: 2025-06-07 (poprzednia sobota, nie dzisiejsza)
    print(f"Test dla '12 czerwca': {parse_human_date('12 czerwca', test_date)}") 