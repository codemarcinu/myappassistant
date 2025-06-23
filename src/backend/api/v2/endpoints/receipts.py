from __future__ import annotations
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List, Optional, Union, Callable, AsyncGenerator, Coroutine

from backend.agents.ocr_agent import OCRAgent, OCRAgentInput
from backend.agents.receipt_analysis_agent import ReceiptAnalysisAgent
from backend.api.v2.exceptions import (
    APIErrorCodes,
    BadRequestError,
    UnprocessableEntityError,
)
from backend.core.database import get_db
from backend.schemas import shopping_schemas
from backend.services.shopping_service import create_shopping_trip

router = APIRouter(prefix="/receipts", tags=["Receipts"])

# Lista dozwolonych typów plików
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
ALLOWED_PDF_TYPES = ["application/pdf"]
ALLOWED_FILE_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_PDF_TYPES


@router.post("/upload", response_model=None)
async def upload_receipt(file: UploadFile = File(...)):
    """Endpoint for uploading and processing receipt images with OCR.

    Returns:
        JSONResponse: Standardized success or error response
    """
    try:
        # Validate file content type
        if not file.content_type:
            raise HTTPException(
                status_code=400,
                detail={
                    "status_code": 400,
                    "error_code": "BAD_REQUEST",
                    "message": "Missing content type header",
                    "details": {
                        "field": "file",
                        "error": "Content-Type header is required",
                    },
                },
            )

        # Sprawdzenie czy typ pliku jest dozwolony
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Unsupported file type",
                    "details": {
                        "content_type": file.content_type,
                        "supported_types": ALLOWED_FILE_TYPES,
                    },
                },
            )

        # Określenie typu pliku dla OCR
        if file.content_type in ALLOWED_IMAGE_TYPES:
            file_type = "image"
        elif file.content_type in ALLOWED_PDF_TYPES:
            file_type = "pdf"
        else:
            # Ten kod nie powinien się wykonać ze względu na wcześniejszą walidację,
            # ale dodajemy go dla pewności
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Unsupported file type",
                    "details": {
                        "content_type": file.content_type,
                        "supported_types": ALLOWED_FILE_TYPES,
                    },
                },
            )

        # Read and process file
        file_bytes = await file.read()
        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=file_bytes, file_type=file_type)
        result = await agent.process(input_data)

        if not result.success:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Failed to process receipt",
                    "details": {
                        "error": result.error,
                        "error_code": "RECEIPT_PROCESSING_ERROR",
                    },
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Receipt processed successfully",
                "data": {"text": result.text, "message": result.message},
            },
        )

    except HTTPException as he:
        # Re-raise HTTPException to preserve the status code and detail
        raise he
    except Exception as e:
        # For other exceptions, return a 500 error with standardized format
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected error processing receipt",
                "details": {"error": str(e)},
            },
        )


@router.post("/analyze", response_model=None)
async def analyze_receipt(ocr_text: str = Form(...)):
    """Analyze OCR text from receipt and extract structured data.

    Returns:
        JSONResponse: Structured receipt data
    """
    try:
        # Process OCR text with ReceiptAnalysisAgent
        analysis_agent = ReceiptAnalysisAgent()
        analysis_result = await analysis_agent.process({"ocr_text": ocr_text})

        if not analysis_result.success:
            raise UnprocessableEntityError(
                message="Failed to analyze receipt data",
                details={
                    "error": analysis_result.error,
                    "error_code": APIErrorCodes.RECEIPT_ANALYSIS_ERROR,
                },
            )

        # Return structured receipt data
        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Receipt analyzed successfully",
                "data": analysis_result.data,
            },
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected error analyzing receipt",
                "details": {"error": str(e)},
            },
        )


@router.post("/save", response_model=None)
async def save_receipt_data(
    receipt_data: shopping_schemas.ShoppingTripCreate,
    db: AsyncSession = Depends(get_db),
):
    """Save analyzed receipt data to database.

    Returns:
        JSONResponse: Result of saving receipt data
    """
    try:
        # Create shopping trip with products in database
        created_trip = await create_shopping_trip(db, receipt_data)

        # Return success response with created trip ID
        return JSONResponse(
            status_code=200,
            content={
                "status_code": 200,
                "message": "Receipt data saved successfully",
                "data": {
                    "trip_id": created_trip.id,
                    "products_count": len(created_trip.products),
                },
            },
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected error saving receipt data",
                "details": {"error": str(e)},
            },
        )
