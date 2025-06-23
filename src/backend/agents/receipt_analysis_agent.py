import json
import logging
import re
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
                    "content": "Jesteś specjalistycznym asystentem do analizy paragonów. Wyciągnij strukturalne dane z tekstu paragonu.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )

        if not response or "message" not in response:
            return AgentResponse(
                success=False,
                error="Nie udało się przeanalizować paragonu z LLM",
            )

        # Parsuj odpowiedź LLM aby wyciągnąć strukturalne dane
        content = response["message"]["content"]
        receipt_data = self._parse_llm_response(content)

        # Zastosuj kategoryzację do produktów
        await self._categorize_products(receipt_data["items"])

        return AgentResponse(
            success=True,
            text="Paragon został pomyślnie przeanalizowany",
            data=receipt_data,
        )

    def _create_receipt_analysis_prompt(self, ocr_text: str) -> str:
        """Tworzy prompt dla LLM do analizy tekstu paragonu"""
        return f"""
        Przeanalizuj poniższy tekst paragonu wyodrębniony przez OCR i wyciągnij strukturalne informacje.

        Tekst paragonu:
        ```
        {ocr_text}
        ```

        Wyciągnij następujące informacje w formacie JSON:
        1. Nazwa sklepu
        2. Data zakupów (format YYYY-MM-DD)
        3. Lista produktów z:
           - Znormalizowana nazwa produktu
           - Ilość
           - Jednostka miary
           - Cena jednostkowa
           - Czy był objęty rabatem
           - Cena końcowa po rabacie
        4. Kwota całkowita

        Odpowiedz TYLKO danymi JSON, bez wyjaśnień ani dodatkowego tekstu.
        """

    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """Parsuje odpowiedź LLM aby wyciągnąć strukturalne dane paragonu"""

        # Wyciągnij JSON z odpowiedzi (na wypadek gdyby LLM dodał inny tekst)
        json_match = re.search(r"({[\s\S]*})", llm_response)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                # Fallback do prostszego parsowania jeśli JSON jest uszkodzony
                data = self._fallback_parse(llm_response)
        else:
            data = self._fallback_parse(llm_response)

        # Upewnij się że wymagane pola istnieją
        return {
            "store_name": data.get("store_name", "Nieznany sklep"),
            "date": data.get("date", ""),
            "total": data.get("total", 0.0),
            "items": data.get("items", []),
        }

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parsowanie gdy wyciąganie JSON nie powiedzie się"""
        # Prosta logika parsowania gdy strukturalne wyciąganie JSON nie powiedzie się

        result: Dict[str, Any] = {
            "store_name": "Nieznany sklep",
            "date": "",
            "total": 0.0,
            "items": [],
        }

        # Spróbuj wyciągnąć nazwę sklepu
        store_match = re.search(r"sklep[:\s]+([^\n]+)", text, re.IGNORECASE)
        if store_match:
            result["store_name"] = store_match.group(1).strip()

        # Spróbuj wyciągnąć datę
        date_match = re.search(r"data[:\s]+([\d-]+)", text, re.IGNORECASE)
        if date_match:
            result["date"] = date_match.group(1).strip()

        # Spróbuj wyciągnąć sumę
        total_match = re.search(r"suma[:\s]+([\d.,]+)", text, re.IGNORECASE)
        if total_match:
            try:
                result["total"] = float(total_match.group(1).replace(",", "."))
            except ValueError:
                pass

        # Spróbuj wyciągnąć produkty (proste podejście)
        items_section = re.search(
            r"produkty[:\s]+([\s\S]+?)(?:suma|$)", text, re.IGNORECASE
        )
        if items_section:
            items_text = items_section.group(1)
            item_matches = re.findall(
                r"([^,\n]+)[,\s]+([\d.,]+)[,\s]+([\d.,]+)", items_text
            )
            for match in item_matches:
                result["items"].append(
                    {
                        "name": match[0].strip(),
                        "quantity": 1.0,
                        "unit_price": float(match[1].replace(",", ".")),
                        "price": float(match[2].replace(",", ".")),
                    }
                )

        return result

    async def _categorize_products(self, items: List[Dict[str, Any]]) -> None:
        """Kategoryzuje produkty używając agenta kategoryzacji"""
        from backend.agents.agent_factory import AgentFactory

        agent_factory = AgentFactory()
        categorization_agent = agent_factory.create_agent("categorization")

        for item in items:
            if not item.get("category") and item.get("name"):
                response = await categorization_agent.process(
                    {"product_name": item["name"]}
                )
                if response.success and response.data:
                    item["category"] = response.data.get("category", "")
