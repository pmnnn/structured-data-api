import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.models.cv import CVData
from app.models.invoice import InvoiceData
from app.models.quote import QuoteData
from app.services.llm import llm_service
from app.services.pdf import extract_text_from_pdf, extract_text_from_docx
from app.database import save_document

router = APIRouter(prefix="/extract", tags=["Extraction"])


class TextInput(BaseModel):
    text: str


class ExtractionResult(BaseModel):
    id: str
    document_type: str
    data: dict


DOCUMENT_TYPES = {
    "cv": CVData,
    "invoice": InvoiceData,
    "quote": QuoteData,
}


async def detect_and_extract(text: str, filename: str = None) -> ExtractionResult:
    doc_type = await llm_service.detect_document_type(text)

    target_model = DOCUMENT_TYPES.get(doc_type)
    if not target_model:
        raise HTTPException(
            status_code=422,
            detail=f"Document type not recognized: {doc_type}"
        )

    result = await llm_service.extract(text, target_model)
    data = result.model_dump()

    doc_id = str(uuid.uuid4())
    await save_document(doc_id, doc_type, data, filename)

    return ExtractionResult(
        id=doc_id,
        document_type=doc_type,
        data=data
    )


@router.post(
    "/text",
    response_model=ExtractionResult,
    summary="Extract any document (plain text)",
    description=(
        "Paste any document as plain text. "
        "The API automatically detects whether it is a CV, invoice, or quote "
        "and returns a clean structured JSON."
    ),
)
async def extract_from_text(body: TextInput) -> ExtractionResult:
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Field 'text' cannot be empty.")
    return await detect_and_extract(body.text)


@router.post(
    "/file",
    response_model=ExtractionResult,
    summary="Extract any document (PDF, DOCX or TXT file)",
    description=(
        "Upload any document file (PDF, DOCX or TXT). "
        "The API automatically detects the document type "
        "and returns a clean structured JSON."
    ),
)
async def extract_from_file(file: UploadFile = File(...)) -> ExtractionResult:
    allowed_extensions = (".pdf", ".docx", ".txt")
    if not file.filename or not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=415,
            detail="Only .pdf, .docx and .txt files are accepted."
        )

    raw = await file.read()

    if file.filename.lower().endswith(".pdf"):
        try:
            text = extract_text_from_pdf(raw)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    elif file.filename.lower().endswith(".docx"):
        try:
            text = extract_text_from_docx(raw)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    else:
        text = raw.decode("utf-8", errors="ignore")

    return await detect_and_extract(text, filename=file.filename)