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
        """Normalizuje datę do formatu YYYY-MM-DD"""
        try:
            date_str = date_str.replace(".", "-").replace(" ", "-")
            parts = date_str.split("-")

            if len(parts) == 3:
                if len(parts[0]) == 4:  # YYYY-MM-DD
                    return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                else:  # DD-MM-YYYY
                    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        except Exception as e:
            logger.warning(f"Błąd normalizacji daty '{date_str}': {e}")

        return ""

    def _validate_and_fix_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Waliduje i poprawia wyciągnięte dane paragonu"""
        # Sprawdź czy suma produktów odpowiada sumie końcowej
        items = data.get("items", [])
        if isinstance(items, list):
            items_total = sum(item.get("total_price", 0) for item in items)
        else:
            items_total = 0.0
        receipt_total = data.get("total_amount", 0)

        # Tolerancja różnicy 1 PLN (zaokrąglenia, rabaty)
        warnings_obj = data.get("validation_warnings", [])
        warnings: list[str] = (
            list(warnings_obj) if isinstance(warnings_obj, list) else []
        )
        if abs(items_total - receipt_total) > 1.0:
            warnings.append(
                f"Różnica między sumą produktów ({items_total:.2f}) a sumą paragonu ({receipt_total:.2f})"
            )
            data["validation_warnings"] = warnings

        # Sprawdź czy data jest w przyszłości
        if data.get("date"):
            try:
                receipt_date = datetime.strptime(data["date"], "%Y-%m-%d")
                if receipt_date > datetime.now():
                    data["date"] = datetime.now().strftime("%Y-%m-%d")
                    warnings_obj2 = data.get("validation_warnings", [])
                    warnings2: list[str] = (
                        list(warnings_obj2) if isinstance(warnings_obj2, list) else []
                    )
                    warnings2.append(
                        "Data paragonu była w przyszłości, ustawiono dzisiejszą"
                    )
                    data["validation_warnings"] = warnings2
            except ValueError:
                data["date"] = ""

        # Upewnij się że wszystkie wymagane pola istnieją
        if "items" not in data:
            data["items"] = []
        if "subtotals" not in data:
            data["subtotals"] = {
                "vat_a_amount": 0,
                "vat_b_amount": 0,
                "vat_c_amount": 0,
                "total_discount": 0,
            }

        return data

    async def _categorize_products(self, items: List[Dict[str, Any]]) -> None:
        """Kategoryzuje produkty używając agenta kategoryzacji"""
        from backend.agents.agent_factory import AgentFactory

        try:
            agent_factory = AgentFactory()
            categorization_agent = agent_factory.create_agent("categorization")

            for item in items:
                if not item.get("category") and item.get("name"):
                    response = await categorization_agent.process(
                        {"product_name": item["name"]}
                    )
                    if response.success and response.data:
                        item["category"] = response.data.get("category", "")
        except Exception as e:
            logger.warning(f"Błąd podczas kategoryzacji produktów: {e}")
            # Nie przerywaj procesu jeśli kategoryzacja się nie powiedzie
