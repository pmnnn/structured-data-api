import json
import logging
from typing import Type, TypeVar

from groq import AsyncGroq
from pydantic import BaseModel, ValidationError

from app.models.cv import CVData
from app.models.invoice import InvoiceData
from app.models.quote import QuoteData

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

CV_SYSTEM_PROMPT = """You are an expert CV analyst. Extract all structured
information from the CV and return ONLY a valid JSON object with EXACTLY
these field names:
{
  "full_name": "...",
  "email": "...",
  "phone": "...",
  "location": "...",
  "linkedin_url": null,
  "summary": null,
  "experiences": [{"company": "...", "position": "...", "start_date": "YYYY-MM", "end_date": null, "description": "..."}],
  "education": [{"institution": "...", "degree": "...", "field_of_study": null, "graduation_year": 2021}],
  "skills": ["..."],
  "languages": ["..."]
}
Use null for missing fields. Return nothing but the JSON."""

INVOICE_SYSTEM_PROMPT = """You are an expert accountant. Extract all structured
information from the invoice and return ONLY a valid JSON object with EXACTLY
these field names:
{
  "invoice_number": "...",
  "invoice_date": "YYYY-MM-DD",
  "due_date": null,
  "currency": "EUR",
  "seller_name": "...",
  "seller_address": null,
  "seller_vat_number": null,
  "buyer_name": "...",
  "buyer_address": null,
  "line_items": [{"description": "...", "quantity": 1.0, "unit_price": 0.0, "total_ht": 0.0, "vat_rate": 20.0}],
  "total_ht": 0.0,
  "total_vat": null,
  "total_ttc": 0.0,
  "payment_method": null,
  "notes": null
}
Convert all amounts to floats. Dates in ISO 8601. Return nothing but the JSON."""

QUOTE_SYSTEM_PROMPT = """You are an expert in commercial quotes. Extract all
structured information from the quote and return ONLY a valid JSON object
with EXACTLY these field names:
{
  "quote_number": "...",
  "quote_date": "YYYY-MM-DD",
  "valid_until": null,
  "currency": "EUR",
  "seller_name": "...",
  "seller_address": null,
  "seller_email": null,
  "seller_phone": null,
  "client_name": "...",
  "client_address": null,
  "line_items": [{"description": "...", "quantity": 1.0, "unit_price": 0.0, "total_ht": 0.0, "discount_percent": null}],
  "total_ht": 0.0,
  "discount_total": null,
  "total_vat": null,
  "total_ttc": 0.0,
  "payment_terms": null,
  "delivery_delay": null,
  "notes": null
}
Convert all amounts to floats. Dates in ISO 8601. Return nothing but the JSON."""

SYSTEM_PROMPTS = {
    CVData: CV_SYSTEM_PROMPT,
    InvoiceData: INVOICE_SYSTEM_PROMPT,
    QuoteData: QUOTE_SYSTEM_PROMPT,
}


class LLMService:
    def __init__(self) -> None:
        self.client = AsyncGroq()
        self.model = "llama-3.3-70b-versatile"

    async def detect_document_type(self, text: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": """You are a document classifier. Analyze the document
regardless of its language (French, English, or any other language),
even if the text has encoding issues or garbled characters.

Look for these clues:
- CV/Resume: names, emails, work experience, education, skills, languages
- Invoice: invoice number, amounts, seller, buyer, payment
- Quote: quote number, services, client, validity date

Return ONLY a JSON object: {"document_type": "cv"} or {"document_type": "invoice"} or {"document_type": "quote"}
Return nothing but the JSON."""
                },
                {
                    "role": "user",
                    "content": f"Classify this document:\n\n{text[:2000]}"
                },
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)
        return data.get("document_type", "unknown")

    async def extract(self, text: str, target_model: Type[T]) -> T:
        system_prompt = SYSTEM_PROMPTS.get(target_model)
        if not system_prompt:
            raise ValueError(f"No prompt defined for {target_model.__name__}")

        logger.info("Calling Groq for %s", target_model.__name__)

        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the document to analyze:\n\n{text}"},
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Groq did not return valid JSON: {exc}") from exc

        try:
            return target_model(**data)
        except ValidationError as exc:
            raise ValueError(f"Invalid data structure: {exc}") from exc


llm_service = LLMService()