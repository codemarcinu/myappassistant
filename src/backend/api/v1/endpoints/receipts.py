from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from backend.agents.ocr_agent import OCRAgent, OCRAgentInput

router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    """Endpoint for uploading and processing receipt images with OCR."""
    try:
        # Read file content
        file_bytes = await file.read()

        # Determine file type
        content_type = file.content_type
        if not content_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing content type header",
            )
        if content_type.startswith("image/"):
            file_type = "image"
        elif content_type == "application/pdf":
            file_type = "pdf"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Only images and PDFs are supported.",
            )

        # Process with OCRAgent
        agent = OCRAgent()
        input_data = OCRAgentInput(file_bytes=file_bytes, file_type=file_type)
        result = await agent.process(input_data)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result.error
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"text": result.text, "message": result.message},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing receipt: {str(e)}",
        )
