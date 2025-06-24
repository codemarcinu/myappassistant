import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List

from backend.agents.base_agent import BaseAgent
from backend.agents.interfaces import AgentResponse
from backend.core.hybrid_llm_client import hybrid_llm_client

logger = logging.getLogger(__name__)


class ReceiptAnalysisAgent(BaseAgent):
    """Agent odpowiedzialny za analizę danych paragonu po przetworzeniu OCR.

    Ten agent analizuje tekst OCR i wyciąga strukturalne informacje:
    - Nazwa sklepu
    - Data zakupów
    - Produkty z znormalizowanymi nazwami
    - Ilości i jednostki miary
    - Ceny jednostkowe
    - Rabaty/promocje
    - Cena całkowita
    - Kategorie produktowe
    """

    def __init__(
        self,
        name: str = "ReceiptAnalysisAgent",
        error_handler=None,
        fallback_manager=None,
        **kwargs,
    ) -> None:
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )

    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        """Przetwarza tekst OCR i wyciąga strukturalne dane paragonu"""

        ocr_text = context.get("ocr_text", "")
        if not ocr_text:
            return AgentResponse(
                success=False,
                error="Brak tekstu OCR do analizy",
            )

        logger.info(
            "Rozpoczynam analizę paragonu",
            extra={"text_length": len(ocr_text), "agent_name": self.name},
        )

        # Użyj LLM do analizy tekstu paragonu
        use_bielik = context.get("use_bielik", True)
        model = (
            "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
            if use_bielik
            else "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        )

        # Utwórz prompt do analizy paragonu
        prompt = self._create_receipt_analysis_prompt(ocr_text)

        # Wywołaj LLM do analizy
        response = await hybrid_llm_client.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś specjalistycznym asystentem do analizy paragonów z polskich sklepów. Wyciągnij strukturalne dane z tekstu paragonu.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )

        if not response or "message" not in response:
            logger.warning("LLM nie zwrócił odpowiedzi, używam fallback parser")
            # Fallback do prostszego parsowania
            receipt_data = self._fallback_parse(ocr_text)
        else:
            # Parsuj odpowiedź LLM aby wyciągnąć strukturalne dane
            content = response["message"]["content"]
            receipt_data = self._parse_llm_response(content)

        # Waliduj i popraw wyciągnięte dane
        receipt_data = self._validate_and_fix_data(receipt_data)

        # Zastosuj kategoryzację do produktów
        await self._categorize_products(receipt_data["items"])

        logger.info(
            "Analiza paragonu zakończona",
            extra={
                "store_name": receipt_data.get("store_name"),
                "items_count": len(receipt_data.get("items", [])),
                "total_amount": receipt_data.get("total_amount", 0),
            },
        )

        return AgentResponse(
            success=True,
            text="Paragon został pomyślnie przeanalizowany",
            data=receipt_data,
        )

    def _create_receipt_analysis_prompt(self, ocr_text: str) -> str:
        """Tworzy zaawansowany prompt dla LLM do analizy polskich paragonów"""
        return f"""
        Przeanalizuj poniższy tekst paragonu z polskiego sklepu i wyciągnij strukturalne informacje.

        TEKST PARAGONU:
        ```
        {ocr_text}
        ```

        INSTRUKCJE SPECJALNE:
        - Szukaj nazw sklepów: Lidl, Auchan, Kaufland, Biedronka, Tesco, Carrefour
        - Format daty może być: DD.MM.YYYY, DD-MM-YYYY, YYYY-MM-DD
        - Ceny mogą być w formacie: XX,XX PLN lub XX,XX A/C (gdzie A/C oznacza stawkę VAT)
        - Produkty mogą mieć kody (np. 571950C, 492359C)
        - Uwzględnij rabaty i promocje (słowa kluczowe: "Rabat", "PROMOCJA", "-")
        - Zwróć uwagę na produkty sprzedawane na wagę (kg, gram)

        WYMAGANY FORMAT JSON:
        {{
            "store_name": "nazwa sklepu",
            "store_address": "adres jeśli dostępny",
            "date": "YYYY-MM-DD",
            "time": "HH:MM jeśli dostępny",
            "receipt_number": "numer paragonu jeśli dostępny",
            "items": [
                {{
                    "name": "znormalizowana nazwa produktu",
                    "original_name": "oryginalna nazwa z paragonu",
                    "product_code": "kod produktu jeśli dostępny",
                    "quantity": liczba,
                    "unit": "szt/kg/g/l",
                    "unit_price": cena_jednostkowa,
                    "total_price": cena_końcowa,
                    "vat_rate": "A/B/C lub 23%/8%/5%",
                    "discount": kwota_rabatu_lub_0,
                    "category": "sugerowana kategoria produktu"
                }}
            ],
            "subtotals": {{
                "vat_a_amount": kwota_vat_23_procent,
                "vat_b_amount": kwota_vat_8_procent,
                "vat_c_amount": kwota_vat_5_procent,
                "total_discount": łączna_kwota_rabatów
            }},
            "total_amount": łączna_kwota,
            "payment_method": "sposób płatności jeśli dostępny"
        }}

        Odpowiedz TYLKO danymi JSON, bez dodatkowych komentarzy.
        """

    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """Parsuje odpowiedź LLM aby wyciągnąć strukturalne dane paragonu"""

        # Wyciągnij JSON z odpowiedzi (na wypadek gdyby LLM dodał inny tekst)
        json_match = re.search(r"({[\s\S]*})", llm_response)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                logger.info("Pomyślnie sparsowano JSON z LLM")
                return self._normalize_data_structure(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Błąd parsowania JSON z LLM: {e}")
                # Fallback do prostszego parsowania jeśli JSON jest uszkodzony
                return self._fallback_parse(llm_response)
        else:
            logger.warning("Nie znaleziono JSON w odpowiedzi LLM, używam fallback")
            return self._fallback_parse(llm_response)

    def _normalize_data_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizuje strukturę danych z LLM"""
        return {
            "store_name": data.get("store_name", "Nieznany sklep"),
            "store_address": data.get("store_address", ""),
            "date": data.get("date", ""),
            "time": data.get("time", ""),
            "receipt_number": data.get("receipt_number", ""),
            "items": data.get("items", []),
            "subtotals": data.get(
                "subtotals",
                {
                    "vat_a_amount": 0,
                    "vat_b_amount": 0,
                    "vat_c_amount": 0,
                    "total_discount": 0,
                },
            ),
            "total_amount": data.get("total_amount", 0.0),
            "payment_method": data.get("payment_method", ""),
        }

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Zaawansowany fallback parser dla polskich paragonów"""
        result = {
            "store_name": "Nieznany sklep",
            "store_address": "",
            "date": "",
            "time": "",
            "receipt_number": "",
            "items": [],
            "subtotals": {
                "vat_a_amount": 0,
                "vat_b_amount": 0,
                "vat_c_amount": 0,
                "total_discount": 0,
            },
            "total_amount": 0.0,
            "payment_method": "",
        }

        # Rozpoznawanie sklepów polskich
        store_patterns = {
            r"lidl": "Lidl",
            r"auchan": "Auchan",
            r"kaufland": "Kaufland",
            r"biedronka": "Biedronka",
            r"tesco": "Tesco",
            r"carrefour": "Carrefour",
        }

        for pattern, store_name in store_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                result["store_name"] = store_name
                break

        # Rozpoznawanie dat (różne formaty polskie)
        date_patterns = [
            r"(\d{2}[-.]?\d{2}[-.]?\d{4})",
            r"(\d{4}[-.]?\d{2}[-.]?\d{2})",
            r"(\d{1,2}[-.]?\d{1,2}[-.]?\d{4})",
        ]

        for pattern in date_patterns:
            date_match = re.search(pattern, text)
            if date_match:
                date_str = date_match.group(1)
                result["date"] = self._normalize_date(date_str)
                break

        # Rozpoznawanie produktów z cenami
        item_patterns = [
            r"([A-ZĄĆĘŁŃÓŚŹŻ][A-ZĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż\s]+)\s+(\d+[,.]?\d*)\s*x?\s*(\d+[,.]?\d*)\s*([A-C]?)",
            r"([A-ZĄĆĘŁŃÓŚŹŻ][^0-9\n]{3,30})\s+(\d+[,.]?\d*)\s*([A-C]?)",
        ]

        for pattern in item_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                if len(match) >= 3:
                    item = {
                        "name": match[0].strip(),
                        "original_name": match[0].strip(),
                        "product_code": "",
                        "quantity": 1.0,
                        "unit": "szt",
                        "unit_price": float(match[-2].replace(",", ".")),
                        "total_price": float(match[-2].replace(",", ".")),
                        "vat_rate": match[-1] if match[-1] else "A",
                        "discount": 0.0,
                        "category": "",
                    }
                    if isinstance(result["items"], list):
                        result["items"].append(item)

        # Rozpoznawanie sumy końcowej
        total_patterns = [
            r"suma\s*pln\s*(\d+[,.]?\d*)",
            r"razem\s*(\d+[,.]?\d*)",
            r"suma\s*(\d+[,.]?\d*)",
        ]

        for pattern in total_patterns:
            total_match = re.search(pattern, text, re.IGNORECASE)
            if total_match:
                result["total_amount"] = float(total_match.group(1).replace(",", "."))
                break

        items_val = result.get("items", [])
        items_count = len(items_val) if isinstance(items_val, list) else 0
        logger.info(f"Fallback parser wyciągnął {items_count} produktów")
        return result

    def _normalize_date(self, date_str: str) -> str:
        """Normalizuje format daty."""
        try:
            # Próba parsowania różnych formatów daty
            if re.match(r"^\d{2}[-.]\d{2}[-.]\d{4}$", date_str):
                return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
            elif re.match(r"^\d{4}[-.]\d{2}[-.]\d{2}$", date_str):
                return datetime.strptime(date_str, "%Y.%m.%d").strftime("%Y-%m-%d")
            elif re.match(r"^\d{1,2}[-.]\d{1,2}[-.]\d{4}$", date_str):
                return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
            return date_str  # Zwróć oryginalny string, jeśli format nie pasuje
        except ValueError:
            return date_str

    def _validate_and_fix_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Waliduje i poprawia wyciągnięte dane paragonu."""
        if "store_name" not in data or not data["store_name"].strip():
            data["store_name"] = "Nieznany Sklep"

        # Normalizacja daty
        if "date" in data and data["date"]:
            data["date"] = self._normalize_date(data["date"])

        # Upewnij się, że 'items' jest listą
        if "items" not in data or not isinstance(data["items"], list):
            data["items"] = []

        # Walidacja i poprawa pozycji
        for item in data["items"]:
            if "name" not in item or not item["name"].strip():
                item["name"] = "Nieznany Produkt"
            if "quantity" in item:
                try:
                    item["quantity"] = float(str(item["quantity"]).replace(",", "."))
                except ValueError:
                    item["quantity"] = 0.0
            if "unit_price" in item:
                try:
                    item["unit_price"] = float(
                        str(item["unit_price"]).replace(",", ".")
                    )
                except ValueError:
                    item["unit_price"] = 0.0
            if "total_price" in item:
                try:
                    item["total_price"] = float(
                        str(item["total_price"]).replace(",", ".")
                    )
                except ValueError:
                    item["total_price"] = 0.0

        # Normalizacja sum i rabatów
        if "total_amount" in data:
            try:
                data["total_amount"] = float(
                    str(data["total_amount"]).replace(",", ".")
                )
            except ValueError:
                data["total_amount"] = 0.0

        if "subtotals" in data and isinstance(data["subtotals"], dict):
            for key in [
                "vat_a_amount",
                "vat_b_amount",
                "vat_c_amount",
                "total_discount",
            ]:
                if key in data["subtotals"]:
                    try:
                        data["subtotals"][key] = float(
                            str(data["subtotals"][key]).replace(",", ".")
                        )
                    except ValueError:
                        data["subtotals"][key] = 0.0

        return data

    async def _categorize_products(self, items: List[Dict[str, Any]]) -> None:
        """Kategoryzuje produkty przy użyciu LLM."""
        if not items:
            return

        product_names = [item["name"] for item in items if "name" in item]
        if not product_names:
            return

        products_to_categorize = ", ".join(product_names)

        categorization_prompt = f"""
        Podaj kategorie dla poniższych produktów. Zwróć tylko listę kategorii, po jednej na produkt, w kolejności.
        Przykładowe kategorie: Owoce, Warzywa, Nabiał, Mięso, Pieczywo, Napoje, Słodycze, Chemia domowa, Kosmetyki, Inne.

        Produkty: {products_to_categorize}

        Odpowiedź (tylko lista kategorii oddzielona przecinkami, bez dodatkowego tekstu):
        """
        try:
            response = await hybrid_llm_client.chat(
                model="SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś ekspertem od kategoryzacji produktów spożywczych.",
                    },
                    {"role": "user", "content": categorization_prompt},
                ],
                stream=False,
                max_tokens=100,
            )
            categories_str = response.get("message", {}).get("content", "").strip()
            categories = [
                cat.strip() for cat in categories_str.split(",") if cat.strip()
            ]

            for i, item in enumerate(items):
                if i < len(categories):
                    item["category"] = categories[i]
                else:
                    item["category"] = "Inne"
        except Exception as e:
            logger.error(f"Błąd podczas kategoryzacji produktów: {e}")
            for item in items:
                item["category"] = "Nieznana"
