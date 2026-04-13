from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.models.cv import CVData
from app.services.llm import llm_service
from app.services.pdf import extract_text_from_pdf

router = APIRouter(prefix="/extract/cv", tags=["CV"])


class TextInput(BaseModel):
    text: str


@router.post("/text", response_model=CVData, summary="Extraire un CV (texte brut)")
async def extract_cv_from_text(body: TextInput) -> CVData:
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Le champ 'text' ne peut pas être vide.")
    try:
        return await llm_service.extract(body.text, CVData)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/pdf", response_model=CVData, summary="Extraire un CV (PDF)")
async def extract_cv_from_pdf(file: UploadFile = File(...)) -> CVData:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Seuls les fichiers .pdf sont acceptés.")

    raw = await file.read()
    try:
        text = extract_text_from_pdf(raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        return await llm_service.extract(text, CVData)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc