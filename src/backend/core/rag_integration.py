"""
RAG Integration Module

This module integrates the existing database (receipts, pantry, meals) with the RAG system
by converting database records into searchable documents.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.crud import get_available_products
from backend.core.rag_document_processor import RAGDocumentProcessor
from backend.models.conversation import Conversation
from backend.services.shopping_service import get_shopping_trips

logger = logging.getLogger(__name__)


class RAGDatabaseIntegration:
    """
    Integrates database data with RAG system by converting records to searchable documents
    """

    def __init__(self, rag_processor: RAGDocumentProcessor) -> None:
        self.rag_processor = rag_processor

    async def sync_receipts_to_rag(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Synchronize all receipts from database to RAG system

        Args:
            db: Database session

        Returns:
            Summary of synchronization results
        """
        try:
            # Get all shopping trips with products
            trips = await get_shopping_trips(db, limit=1000)

            # Zamień ORM na dict, aby nie trzymać referencji do sesji
            trips_data = []
            for trip in trips:
                trip_dict = {
                    "id": trip.id,
                    "store_name": trip.store_name,
                    "trip_date": trip.trip_date,
                    "total_amount": trip.total_amount,
                    "products": [
                        {
                            "name": p.name,
                            "quantity": p.quantity,
                            "unit_price": p.unit_price,
                            "category": getattr(p, "category", None),
                        }
                        for p in getattr(trip, "products", [])
                    ],
                }
                trips_data.append(trip_dict)

            total_chunks = 0
            processed_trips = 0

            for trip in trips_data:
                # Create document content from trip
                content = self._format_receipt_content(trip)
                metadata = self._create_receipt_metadata(trip)

                # Process with RAG
                chunks = await self.rag_processor.process_document(
                    content=content,
                    source_id=f"receipt_{trip['id']}",
                    metadata=metadata,
                )

                total_chunks += len(chunks)
                processed_trips += 1

            return {
                "success": True,
                "processed_trips": processed_trips,
                "total_chunks": total_chunks,
                "message": f"Successfully synced {processed_trips} receipts to RAG",
            }

        except Exception as e:
            logger.error(f"Error syncing receipts to RAG: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_trips": 0,
                "total_chunks": 0,
            }

    async def sync_pantry_to_rag(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Synchronize pantry state to RAG system

        Args:
            db: Database session

        Returns:
            Summary of synchronization results
        """
        try:
            products = await get_available_products(db)
            # Zamień ORM na dict
            products_data = [
                {
                    "name": p.name,
                    "quantity": p.quantity,
                    "expiration_date": getattr(p, "expiration_date", None),
                    "category": getattr(p, "category", None),
                }
                for p in products
            ]
            if not products_data:
                return {
                    "success": True,
                    "processed_products": 0,
                    "total_chunks": 0,
                    "message": "No products in pantry to sync",
                }

            # Create document content from pantry
            content = self._format_pantry_content(products_data)
            metadata = self._create_pantry_metadata(products_data)

            # Process with RAG
            chunks = await self.rag_processor.process_document(
                content=content, source_id="pantry_state", metadata=metadata
            )

            return {
                "success": True,
                "processed_products": len(products_data),
                "total_chunks": len(chunks),
                "message": f"Successfully synced {len(products_data)} products to RAG",
            }

        except Exception as e:
            logger.error(f"Error syncing pantry to RAG: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_products": 0,
                "total_chunks": 0,
            }

    async def sync_conversations_to_rag(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Synchronize conversation history to RAG system

        Args:
            db: Database session

        Returns:
            Summary of synchronization results
        """
        try:
            stmt = (
                select(Conversation).order_by(Conversation.created_at.desc()).limit(100)
            )
            result = await db.execute(stmt)
            conversations = result.scalars().all()
            # Zamień ORM na dict
            conversations_data = [
                {
                    "id": c.id,
                    "created_at": c.created_at,
                    "user_message": c.user_message,
                    "assistant_response": c.assistant_response,
                    "intent_type": getattr(c, "intent_type", None),
                    "session_id": getattr(c, "session_id", None),
                }
                for c in conversations
            ]
            total_chunks = 0
            processed_conversations = 0

            for conv in conversations_data:
                # Create document content from conversation
                content = self._format_conversation_content(conv)
                metadata = self._create_conversation_metadata(conv)

                # Process with RAG
                chunks = await self.rag_processor.process_document(
                    content=content,
                    source_id=f"conversation_{conv['id']}",
                    metadata=metadata,
                )

                total_chunks += len(chunks)
                processed_conversations += 1

            return {
                "success": True,
                "processed_conversations": processed_conversations,
                "total_chunks": total_chunks,
                "message": f"Successfully synced {processed_conversations} conversations to RAG",
            }

        except Exception as e:
            logger.error(f"Error syncing conversations to RAG: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_conversations": 0,
                "total_chunks": 0,
            }

    async def sync_all_to_rag(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Synchronize all database data to RAG system

        Args:
            db: Database session

        Returns:
            Summary of all synchronization results
        """
        results = {}

        # Sync receipts
        results["receipts"] = await self.sync_receipts_to_rag(db)

        # Sync pantry
        results["pantry"] = await self.sync_pantry_to_rag(db)

        # Sync conversations
        results["conversations"] = await self.sync_conversations_to_rag(db)

        # Calculate totals
        total_chunks = sum(
            r.get("total_chunks", 0) for r in results.values() if r.get("success")
        )
        all_successful = all(r.get("success", False) for r in results.values())

        return {
            "success": all_successful,
            "results": results,
            "total_chunks": total_chunks,
            "message": f"Sync completed with {total_chunks} total chunks",
        }

    def _format_receipt_content(self, trip: dict) -> str:
        """Format shopping trip as document content"""
        products_text = "\n".join(
            [
                f"- {product['name']}: {product['quantity']} szt. @ {product['unit_price']} zł"
                for product in trip["products"]
            ]
        )

        return f"""
Paragon z {trip['store_name']} z dnia {trip['trip_date']}

Produkty:
{products_text}

Suma: {trip['total_amount']} zł
"""

    def _create_receipt_metadata(self, trip: dict) -> Dict[str, Any]:
        """Create metadata for receipt document"""
        return {
            "type": "receipt",
            "store": trip["store_name"],
            "date": trip["trip_date"].isoformat(),
            "total_amount": trip["total_amount"],
            "products_count": len(trip["products"]),
            "categories": list(
                set(
                    product["category"]
                    for product in trip["products"]
                    if product["category"]
                )
            ),
        }

    def _format_pantry_content(self, products: List[dict]) -> str:
        """Format pantry products as document content"""
        products_text = "\n".join(
            [
                f"- {product['name']}: {product['quantity']} szt. (wygasa: {product['expiration_date']})"
                for product in products
            ]
        )

        return f"""
Stan spiżarni - ostatnia aktualizacja: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Dostępne produkty:
{products_text}

Łącznie: {len(products)} produktów
"""

    def _create_pantry_metadata(self, products: List[dict]) -> Dict[str, Any]:
        """Create metadata for pantry document"""
        categories = list(
            set(product["category"] for product in products if product["category"])
        )
        expiry_dates = [
            product["expiration_date"]
            for product in products
            if product["expiration_date"]
        ]

        return {
            "type": "pantry",
            "last_updated": datetime.now().isoformat(),
            "total_items": len(products),
            "categories": categories,
            "expiring_soon": len(
                [d for d in expiry_dates if d and (d - datetime.now().date()).days <= 7]
            ),
        }

    def _format_conversation_content(self, conversation: dict) -> str:
        """Format conversation as document content"""
        return f"""
Rozmowa z {conversation['created_at'].strftime('%Y-%m-%d %H:%M')}

Pytanie: {conversation['user_message']}
Odpowiedź: {conversation['assistant_response']}

Typ: {conversation['intent_type']}
"""

    def _create_conversation_metadata(self, conversation: dict) -> Dict[str, Any]:
        """Create metadata for conversation document"""
        return {
            "type": "conversation",
            "date": conversation["created_at"].isoformat(),
            "intent_type": conversation["intent_type"],
            "session_id": conversation["session_id"],
        }


# Global instance
rag_integration = RAGDatabaseIntegration(RAGDocumentProcessor())
