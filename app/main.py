import logging
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import extract, dashboard
from app.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Structured Data Extraction API",
    description=(
        "Transforms unstructured documents (CVs, invoices, quotes) "
        "into clean JSON objects, ready to be inserted into a CRM or ERP.\n\n"
        "**Supported formats**: PDF, DOCX, TXT\n\n"
        "**Supported document types**: CV, Invoice, Quote\n\n"
        "The API automatically detects the document type."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Database initialized")


app.include_router(extract.router)
app.include_router(dashboard.router)


@app.get("/health", tags=["Monitoring"], summary="Check server status")
async def health_check():
    return {"status": "ok", "version": app.version}


@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")