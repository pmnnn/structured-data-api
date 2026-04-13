import uuid
import json
import logging
from typing import List
from fastapi import APIRouter, Query, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from app.database import get_all_documents, save_document, delete_document, update_document
from app.services.pdf import extract_text_from_pdf, extract_text_from_docx
from app.services.llm import llm_service
from app.models.cv import CVData
from app.models.invoice import InvoiceData
from app.models.quote import QuoteData

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Dashboard"])

DOCUMENT_TYPES = {
    "cv": CVData,
    "invoice": InvoiceData,
    "quote": QuoteData,
}


def manual_form_page(filename: str = ""):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manual Entry</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: sans-serif; background: #f5f5f5; }}
            header {{ background: #1a1a2e; color: white; padding: 20px 40px; }}
            header h1 {{ font-size: 22px; }}
            header p {{ opacity: 0.7; font-size: 14px; margin-top: 4px; }}
            .container {{ padding: 30px 40px; max-width: 800px; }}
            .alert {{ background: #fff3e0; border-left: 4px solid #f57c00; padding: 16px 20px; border-radius: 8px; margin-bottom: 24px; }}
            .alert h3 {{ color: #e65100; margin-bottom: 6px; }}
            .alert p {{ color: #555; font-size: 14px; }}
            .card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .tabs {{ display: flex; gap: 8px; margin-bottom: 24px; }}
            .tab {{ padding: 8px 20px; border-radius: 20px; border: 1px solid #ddd; background: white; cursor: pointer; font-size: 14px; color: #555; }}
            .tab.active {{ background: #1a1a2e; color: white; border-color: #1a1a2e; }}
            .form-section {{ display: none; }}
            .form-section.active {{ display: block; }}
            .form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
            .form-group {{ display: flex; flex-direction: column; gap: 6px; }}
            .form-group.full {{ grid-column: 1 / -1; }}
            label {{ font-size: 13px; color: #555; font-weight: 500; }}
            input, textarea, select {{ border: 1px solid #ddd; border-radius: 8px; padding: 10px 12px; font-size: 14px; width: 100%; }}
            textarea {{ height: 80px; resize: vertical; }}
            .section-title {{ font-size: 13px; font-weight: bold; color: #1a1a2e; margin: 20px 0 12px; padding-bottom: 6px; border-bottom: 1px solid #eee; grid-column: 1 / -1; }}
            .btn {{ background: #1a1a2e; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; }}
            .btn:hover {{ background: #2d2d4e; }}
            .btn-cancel {{ background: #f0f0f0; color: #555; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; }}
            .footer {{ display: flex; gap: 12px; margin-top: 24px; }}
        </style>
    </head>
    <body>
        <header>
            <h1>📄 Manual Entry</h1>
            <p>Document not recognized — please fill in the details manually</p>
        </header>
        <div class="container">
            <div class="alert">
                <h3>⚠️ Document not recognized</h3>
                <p>The file <strong>{filename}</strong> could not be automatically classified. Please select the document type and fill in the fields manually.</p>
            </div>
            <div class="card">
                <div class="tabs">
                    <button class="tab active" onclick="switchTab('cv', event)">👤 CV</button>
                    <button class="tab" onclick="switchTab('invoice', event)">🧾 Invoice</button>
                    <button class="tab" onclick="switchTab('quote', event)">📋 Quote</button>
                </div>

                <!-- CV Form -->
                <form class="form-section active" id="form-cv" action="/dashboard/manual" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="doc_type" value="cv">
                    <div class="form-grid">
                        <div class="section-title">Personal information</div>
                        <div class="form-group"><label>Full name *</label><input type="text" name="full_name" required></div>
                        <div class="form-group"><label>Email</label><input type="email" name="email"></div>
                        <div class="form-group"><label>Phone</label><input type="text" name="phone"></div>
                        <div class="form-group"><label>Location</label><input type="text" name="location"></div>
                        <div class="form-group full"><label>LinkedIn URL</label><input type="text" name="linkedin_url"></div>
                        <div class="form-group full"><label>Summary</label><textarea name="summary"></textarea></div>
                        <div class="section-title">Skills & languages</div>
                        <div class="form-group full"><label>Skills (comma separated)</label><input type="text" name="skills" placeholder="Python, FastAPI, Docker..."></div>
                        <div class="form-group full"><label>Languages (comma separated)</label><input type="text" name="languages" placeholder="French, English..."></div>
                        <div class="section-title">Attachment</div>
                        <div class="form-group full"><label>Attach original file</label><input type="file" name="file" accept=".pdf,.docx,.txt"></div>
                    </div>
                    <div class="footer">
                        <a href="/dashboard"><button type="button" class="btn-cancel">Cancel</button></a>
                        <button type="submit" class="btn">Save →</button>
                    </div>
                </form>

                <!-- Invoice Form -->
                <form class="form-section" id="form-invoice" action="/dashboard/manual" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="doc_type" value="invoice">
                    <div class="form-grid">
                        <div class="section-title">Invoice details</div>
                        <div class="form-group"><label>Invoice number *</label><input type="text" name="invoice_number" required></div>
                        <div class="form-group"><label>Invoice date *</label><input type="date" name="invoice_date" required></div>
                        <div class="form-group"><label>Due date</label><input type="date" name="due_date"></div>
                        <div class="form-group"><label>Currency</label><select name="currency"><option>EUR</option><option>USD</option><option>GBP</option><option>SGD</option></select></div>
                        <div class="section-title">Seller</div>
                        <div class="form-group"><label>Seller name *</label><input type="text" name="seller_name" required></div>
                        <div class="form-group"><label>VAT number</label><input type="text" name="seller_vat_number"></div>
                        <div class="form-group full"><label>Seller address</label><input type="text" name="seller_address"></div>
                        <div class="section-title">Buyer</div>
                        <div class="form-group"><label>Buyer name *</label><input type="text" name="buyer_name" required></div>
                        <div class="form-group full"><label>Buyer address</label><input type="text" name="buyer_address"></div>
                        <div class="section-title">Totals</div>
                        <div class="form-group"><label>Total HT *</label><input type="number" step="0.01" name="total_ht" required></div>
                        <div class="form-group"><label>Total VAT</label><input type="number" step="0.01" name="total_vat"></div>
                        <div class="form-group"><label>Total TTC *</label><input type="number" step="0.01" name="total_ttc" required></div>
                        <div class="form-group"><label>Payment method</label><input type="text" name="payment_method"></div>
                        <div class="section-title">Attachment</div>
                        <div class="form-group full"><label>Attach original file</label><input type="file" name="file" accept=".pdf,.docx,.txt"></div>
                    </div>
                    <div class="footer">
                        <a href="/dashboard"><button type="button" class="btn-cancel">Cancel</button></a>
                        <button type="submit" class="btn">Save →</button>
                    </div>
                </form>

                <!-- Quote Form -->
                <form class="form-section" id="form-quote" action="/dashboard/manual" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="doc_type" value="quote">
                    <div class="form-grid">
                        <div class="section-title">Quote details</div>
                        <div class="form-group"><label>Quote number *</label><input type="text" name="quote_number" required></div>
                        <div class="form-group"><label>Quote date *</label><input type="date" name="quote_date" required></div>
                        <div class="form-group"><label>Valid until</label><input type="date" name="valid_until"></div>
                        <div class="form-group"><label>Currency</label><select name="currency"><option>EUR</option><option>USD</option><option>GBP</option><option>SGD</option></select></div>
                        <div class="section-title">Seller</div>
                        <div class="form-group"><label>Seller name *</label><input type="text" name="seller_name" required></div>
                        <div class="form-group"><label>Seller email</label><input type="email" name="seller_email"></div>
                        <div class="form-group"><label>Seller phone</label><input type="text" name="seller_phone"></div>
                        <div class="form-group full"><label>Seller address</label><input type="text" name="seller_address"></div>
                        <div class="section-title">Client</div>
                        <div class="form-group"><label>Client name *</label><input type="text" name="client_name" required></div>
                        <div class="form-group full"><label>Client address</label><input type="text" name="client_address"></div>
                        <div class="section-title">Totals</div>
                        <div class="form-group"><label>Total HT *</label><input type="number" step="0.01" name="total_ht" required></div>
                        <div class="form-group"><label>Total VAT</label><input type="number" step="0.01" name="total_vat"></div>
                        <div class="form-group"><label>Total TTC *</label><input type="number" step="0.01" name="total_ttc" required></div>
                        <div class="form-group"><label>Payment terms</label><input type="text" name="payment_terms"></div>
                        <div class="form-group"><label>Delivery delay</label><input type="text" name="delivery_delay"></div>
                        <div class="section-title">Attachment</div>
                        <div class="form-group full"><label>Attach original file</label><input type="file" name="file" accept=".pdf,.docx,.txt"></div>
                    </div>
                    <div class="footer">
                        <a href="/dashboard"><button type="button" class="btn-cancel">Cancel</button></a>
                        <button type="submit" class="btn">Save →</button>
                    </div>
                </form>
            </div>
        </div>
        <script>
            function switchTab(type, event) {{
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.form-section').forEach(f => f.classList.remove('active'));
                document.getElementById('form-' + type).classList.add('active');
                event.target.classList.add('active');
            }}
        </script>
    </body>
    </html>
    """


def results_page(success_count: int, failed: list, back_url: str = "/home") -> str:
    failed_cards = ""
    for f in failed:
        name = f["filename"]
        reason = f["reason"]
        failed_cards += f"""
        <div class="fail-card">
            <div class="fail-info">
                <span class="fail-icon">⚠️</span>
                <div>
                    <strong>{name}</strong>
                    <p>{reason}</p>
                </div>
            </div>
            <a href="/dashboard/manual?filename={name}" class="btn-manual">Remplir manuellement →</a>
        </div>"""

    success_banner = f"""
        <div class="banner success">
            ✅ <strong>{success_count} fichier(s)</strong> extrait(s) avec succès.
            <a href="/dashboard">Voir le dashboard →</a>
        </div>""" if success_count else ""

    return f"""<!DOCTYPE html>
    <html>
    <head>
        <title>Résultats d'import</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: sans-serif; background: #f5f5f5; }}
            header {{ background: #1a1a2e; color: white; padding: 20px 40px; }}
            header h1 {{ font-size: 22px; }}
            .container {{ padding: 30px 40px; max-width: 800px; }}
            .banner {{ padding: 16px 20px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }}
            .banner.success {{ background: #e8f5e9; border-left: 4px solid #2e7d32; color: #1b5e20; }}
            .banner a {{ color: #2e7d32; font-weight: bold; margin-left: 12px; }}
            .section-title {{ font-size: 15px; font-weight: bold; color: #c0392b; margin-bottom: 14px; }}
            .fail-card {{ background: white; border-radius: 10px; padding: 16px 20px; margin-bottom: 12px;
                          box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; justify-content: space-between;
                          align-items: center; gap: 16px; }}
            .fail-info {{ display: flex; align-items: flex-start; gap: 12px; }}
            .fail-icon {{ font-size: 20px; }}
            .fail-info strong {{ font-size: 14px; color: #1a1a2e; }}
            .fail-info p {{ font-size: 12px; color: #888; margin-top: 3px; }}
            .btn-manual {{ background: #1a1a2e; color: white; text-decoration: none; padding: 8px 16px;
                           border-radius: 8px; font-size: 13px; white-space: nowrap; }}
            .btn-manual:hover {{ background: #2d2d4e; }}
            .btn-back {{ display: inline-block; margin-top: 24px; color: #555; font-size: 13px; text-decoration: none; }}
        </style>
    </head>
    <body>
        <header><h1>📋 Résultats d'import</h1></header>
        <div class="container">
            {success_banner}
            {"<div class='section-title'>Fichiers non reconnus</div>" + failed_cards if failed else ""}
            <a class="btn-back" href="{back_url}">← Retour au dashboard</a>
        </div>
    </body>
    </html>"""


@router.get("/dashboard/manual", include_in_schema=False)
async def manual_form_get(filename: str = ""):
    return HTMLResponse(content=manual_form_page(filename))


@router.delete("/dashboard/documents/{doc_id}", include_in_schema=False)
async def delete_doc(doc_id: str):
    await delete_document(doc_id)
    return {"ok": True}


@router.put("/dashboard/documents/{doc_id}", include_in_schema=False)
async def update_doc(doc_id: str, request: Request):
    data = await request.json()
    await update_document(doc_id, data)
    return {"ok": True}


@router.get("/documents", summary="List all extracted documents")
async def list_documents(document_type: str = Query(None)):
    docs = await get_all_documents(document_type)
    return {"total": len(docs), "documents": docs}


@router.post("/dashboard/manual", include_in_schema=False)
async def manual_entry(request: Request, file: UploadFile = File(None)):
    from fastapi.responses import RedirectResponse
    form = await request.form()
    doc_type = form.get("doc_type")
    filename = file.filename if file and file.filename else None

    if doc_type == "cv":
        skills_raw = form.get("skills", "")
        languages_raw = form.get("languages", "")
        data = {
            "full_name": form.get("full_name"),
            "email": form.get("email") or None,
            "phone": form.get("phone") or None,
            "location": form.get("location") or None,
            "linkedin_url": form.get("linkedin_url") or None,
            "summary": form.get("summary") or None,
            "experiences": [],
            "education": [],
            "skills": [s.strip() for s in skills_raw.split(",") if s.strip()],
            "languages": [l.strip() for l in languages_raw.split(",") if l.strip()],
        }
    elif doc_type == "invoice":
        data = {
            "invoice_number": form.get("invoice_number"),
            "invoice_date": form.get("invoice_date"),
            "due_date": form.get("due_date") or None,
            "currency": form.get("currency", "EUR"),
            "seller_name": form.get("seller_name"),
            "seller_address": form.get("seller_address") or None,
            "seller_vat_number": form.get("seller_vat_number") or None,
            "buyer_name": form.get("buyer_name"),
            "buyer_address": form.get("buyer_address") or None,
            "line_items": [],
            "total_ht": float(form.get("total_ht") or 0),
            "total_vat": float(form.get("total_vat")) if form.get("total_vat") else None,
            "total_ttc": float(form.get("total_ttc") or 0),
            "payment_method": form.get("payment_method") or None,
            "notes": None,
        }
    elif doc_type == "quote":
        data = {
            "quote_number": form.get("quote_number"),
            "quote_date": form.get("quote_date"),
            "valid_until": form.get("valid_until") or None,
            "currency": form.get("currency", "EUR"),
            "seller_name": form.get("seller_name"),
            "seller_address": form.get("seller_address") or None,
            "seller_email": form.get("seller_email") or None,
            "seller_phone": form.get("seller_phone") or None,
            "client_name": form.get("client_name"),
            "client_address": form.get("client_address") or None,
            "line_items": [],
            "total_ht": float(form.get("total_ht") or 0),
            "discount_total": None,
            "total_vat": float(form.get("total_vat")) if form.get("total_vat") else None,
            "total_ttc": float(form.get("total_ttc") or 0),
            "payment_terms": form.get("payment_terms") or None,
            "delivery_delay": form.get("delivery_delay") or None,
            "notes": None,
        }
    else:
        return RedirectResponse(url=redirect_url, status_code=303)

    doc_id = str(uuid.uuid4())
    await save_document(doc_id, doc_type, data, filename)
    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/dashboard/upload", include_in_schema=False)
async def upload_from_dashboard(files: List[UploadFile] = File(None), text: str = Form(None), space: str = Form("hr")):
    from fastapi.responses import RedirectResponse

    redirect_url = f"/dashboard/{space}"
    failed = []
    success_count = 0

    # Handle pasted text
    if text and text.strip():
        doc_type = await llm_service.detect_document_type(text)
        target_model = DOCUMENT_TYPES.get(doc_type)
        if not target_model:
            failed.append({"filename": "texte collé", "reason": "Type de document non reconnu"})
        else:
            try:
                result = await llm_service.extract(text, target_model)
                await save_document(str(uuid.uuid4()), doc_type, result.model_dump(), None)
                success_count += 1
            except Exception as e:
                logger.error("Extraction failed for pasted text: %s", e, exc_info=True)
                failed.append({"filename": "texte collé", "reason": "Extraction échouée"})

    # Handle file uploads
    for file in (files or []):
        if not file or not file.filename:
            continue
        try:
            raw = await file.read()
            if file.filename.lower().endswith(".pdf"):
                content = extract_text_from_pdf(raw)
            elif file.filename.lower().endswith(".docx"):
                content = extract_text_from_docx(raw)
            else:
                content = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            failed.append({"filename": file.filename, "reason": f"Lecture impossible : {e}"})
            continue

        try:
            doc_type = await llm_service.detect_document_type(content)
            target_model = DOCUMENT_TYPES.get(doc_type)
            if not target_model:
                failed.append({"filename": file.filename, "reason": "Type de document non reconnu"})
                continue
            result = await llm_service.extract(content, target_model)
            await save_document(str(uuid.uuid4()), doc_type, result.model_dump(), file.filename)
            success_count += 1
        except Exception as e:
            logger.error("Extraction failed for %s: %s", file.filename, e, exc_info=True)
            reason = "Limite d'API atteinte, réessaie dans quelques minutes" if "429" in str(e) else "Extraction échouée"
            failed.append({"filename": file.filename, "reason": reason})

    if not failed:
        return RedirectResponse(url=redirect_url, status_code=303)

    return HTMLResponse(content=results_page(success_count, failed, redirect_url))


@router.post("/dashboard/chat", include_in_schema=False)
async def dashboard_chat(request: Request):
    body = await request.json()
    message = body.get("message", "")
    history = body.get("history", [])

    docs = await get_all_documents()
    docs_summary = [
        {
            "id": d["id"],
            "type": d["document_type"],
            "filename": d.get("filename"),
            "created_at": d["created_at"][:10],
            # CV fields
            "full_name": d["data"].get("full_name"),
            # Invoice fields
            "invoice_number": d["data"].get("invoice_number"),
            "seller_name": d["data"].get("seller_name"),
            "buyer_name": d["data"].get("buyer_name"),
            # Quote fields
            "quote_number": d["data"].get("quote_number"),
            "client_name": d["data"].get("client_name"),
        }
        for d in docs
    ]

    count_by_type = {}
    for d in docs_summary:
        t = d["type"]
        count_by_type[t] = count_by_type.get(t, 0) + 1

    system_prompt = f"""You are an assistant embedded in a document management dashboard. You help the user manage extracted documents (CVs, invoices, quotes).

CRITICAL LANGUAGE RULE: Detect the language of the user's message and respond in THAT EXACT language. If the user writes in French, respond in French. If in English, respond in English. Never mix languages.

DOCUMENT COUNTS (authoritative — use these exact numbers, never recount):
- CVs: {count_by_type.get('cv', 0)}
- Invoices: {count_by_type.get('invoice', 0)}
- Quotes: {count_by_type.get('quote', 0)}
- Total: {len(docs_summary)}

Current documents ({len(docs_summary)}) — use ALL fields below to search and find documents accurately:
{json.dumps(docs_summary, ensure_ascii=False, indent=2)}

Available actions:
- delete_document : params {{ "doc_id": "...", "doc_name": "..." }}
- delete_documents : params {{ "doc_ids": ["...", "..."], "names": ["...", "..."] }}
- update_field : params {{ "doc_id": "...", "field": "...", "value": "...", "doc_name": "..." }}
- show_document : params {{ "doc_id": "..." }} (no confirmation needed, single doc)
- show_documents : params {{ "doc_ids": ["...", "..."] }} (no confirmation needed, multiple docs)

Respond ONLY in JSON:
{{
  "message": "Your clear message to the user (in user's language)",
  "action": null,
  "requires_confirmation": false
}}

Or with an action:
{{
  "message": "What you are about to do",
  "action": {{
    "type": "delete_documents",
    "params": {{"doc_ids": ["id1"], "names": ["Name 1"]}},
    "description": "Delete 1 duplicate: Name 1"
  }},
  "requires_confirmation": true
}}

Rules:
- Always require confirmation (requires_confirmation: true) before delete or update
- show_document does not require confirmation
- To find duplicates, compare full_name / seller_name / invoice_number across documents
- When counting by document type (e.g. "how many CVs", "combien de CV"), ALWAYS filter by the `type` field first ("cv", "invoice", or "quote"), then apply any additional criteria
- When counting (e.g. "how many invoices from Airbus"), filter by type == "invoice" first, then search seller_name AND buyer_name AND client_name fields
- Be concise"""

    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    response = await llm_service.client.chat.completions.create(
        model=llm_service.model,
        response_format={"type": "json_object"},
        messages=messages,
        temperature=0.3,
    )
    return json.loads(response.choices[0].message.content)


@router.post("/dashboard/execute", include_in_schema=False)
async def execute_action(request: Request):
    body = await request.json()
    action = body.get("action", {})
    action_type = action.get("type")
    params = action.get("params", {})

    if action_type == "delete_document":
        await delete_document(params["doc_id"])
        return {"ok": True, "message": f"Document \"{params.get('doc_name', '')}\" supprimé.", "reload": True}

    elif action_type == "delete_documents":
        for doc_id in params.get("doc_ids", []):
            await delete_document(doc_id)
        names = ", ".join(params.get("names", []))
        count = len(params.get("doc_ids", []))
        return {"ok": True, "message": f"{count} document(s) supprimé(s) : {names}", "reload": True}

    elif action_type == "update_field":
        docs = await get_all_documents()
        doc = next((d for d in docs if d["id"] == params["doc_id"]), None)
        if doc:
            doc["data"][params["field"]] = params["value"]
            await update_document(params["doc_id"], doc["data"])
        return {"ok": True, "message": f"Champ mis à jour.", "reload": True}

    elif action_type == "show_document":
        return {"ok": True, "message": f"Clique sur le document dans le tableau pour l'afficher.", "reload": False}

    return {"ok": False, "message": "Action non reconnue.", "reload": False}


@router.get("/home", response_class=HTMLResponse, include_in_schema=False)
async def home():
    all_docs = await get_all_documents()
    n_cv = sum(1 for d in all_docs if d["document_type"] == "cv")
    n_inv = sum(1 for d in all_docs if d["document_type"] == "invoice")
    n_quo = sum(1 for d in all_docs if d["document_type"] == "quote")
    return f"""<!DOCTYPE html>
    <html>
    <head>
        <title>Accueil</title>
        <style>
            * {{ box-sizing:border-box; margin:0; padding:0; }}
            body {{ font-family:sans-serif; background:#f5f5f5; min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; }}
            h1 {{ font-size:26px; color:#1a1a2e; margin-bottom:8px; text-align:center; }}
            p.sub {{ color:#888; font-size:14px; margin-bottom:48px; text-align:center; }}
            .cards {{ display:flex; gap:24px; }}
            .card {{ background:white; border-radius:16px; padding:36px 40px; width:260px; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.08); cursor:pointer; text-decoration:none; transition:transform .15s, box-shadow .15s; border-top:4px solid transparent; }}
            .card:hover {{ transform:translateY(-4px); box-shadow:0 8px 24px rgba(0,0,0,0.12); }}
            .card.hr {{ border-color:#1a73e8; }}
            .card.finance {{ border-color:#2e7d32; }}
            .card-icon {{ font-size:40px; margin-bottom:16px; }}
            .card h2 {{ font-size:18px; color:#1a1a2e; margin-bottom:6px; }}
            .card p {{ font-size:13px; color:#888; margin-bottom:20px; }}
            .card-count {{ font-size:28px; font-weight:bold; }}
            .card.hr .card-count {{ color:#1a73e8; }}
            .card.finance .card-count {{ color:#2e7d32; }}
            .card-count-label {{ font-size:11px; color:#aaa; margin-top:2px; }}
        </style>
    </head>
    <body>
        <h1>📄 Extraction Dashboard</h1>
        <p class="sub">Choisissez votre espace de travail</p>
        <div class="cards">
            <a href="/dashboard/hr" class="card hr">
                <div class="card-icon">👥</div>
                <h2>Espace RH</h2>
                <p>Gestion des candidatures et CV</p>
                <div class="card-count">{n_cv}</div>
                <div class="card-count-label">CV enregistré(s)</div>
            </a>
            <a href="/dashboard/finance" class="card finance">
                <div class="card-icon">💰</div>
                <h2>Espace Finance</h2>
                <p>Gestion des factures et devis</p>
                <div class="card-count">{n_inv + n_quo}</div>
                <div class="card-count-label">document(s) financier(s)</div>
            </a>
        </div>
    </body>
    </html>"""


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/home")


async def render_dashboard(space: str, type_filter: str = None):
    if space == "hr":
        allowed_types = ["cv"]
        title = "Espace RH"
        subtitle = "Gestion des candidatures"
        accent = "#1a73e8"
        dash_url = "/dashboard/hr"
        chat_intro = "Bonjour ! Je suis votre assistant RH. Je peux vous aider à retrouver des CV, supprimer des doublons, mettre à jour des informations…"
        filters_html = f"""<a href="/dashboard/hr" {"class='active'" if not type_filter else ""}>Tous les CV</a>"""
        stats_html = f"""
            <div class="stat"><h2>{{}}</h2><p>CV au total</p></div>
        """
    else:
        allowed_types = ["invoice", "quote"]
        title = "Espace Finance"
        subtitle = "Gestion des factures et devis"
        accent = "#2e7d32"
        dash_url = "/dashboard/finance"
        chat_intro = "Bonjour ! Je suis votre assistant Finance. Je peux vous aider à retrouver des factures, des devis, supprimer des doublons…"
        filters_html = f"""
            <a href="/dashboard/finance" {"class='active'" if not type_filter else ""}>Tous</a>
            <a href="/dashboard/finance?type=invoice" {"class='active'" if type_filter == 'invoice' else ""}>Factures</a>
            <a href="/dashboard/finance?type=quote" {"class='active'" if type_filter == 'quote' else ""}>Devis</a>
        """

    all_docs = await get_all_documents(type_filter)
    docs = [d for d in all_docs if d["document_type"] in allowed_types]
    docs_json = json.dumps(docs)

    if space == "hr":
        stats_html = f'<div class="stat"><h2>{len(docs)}</h2><p>CV enregistrés</p></div>'
    else:
        n_inv = sum(1 for d in docs if d["document_type"] == "invoice")
        n_quo = sum(1 for d in docs if d["document_type"] == "quote")
        stats_html = f"""
            <div class="stat"><h2>{len(docs)}</h2><p>Total</p></div>
            <div class="stat"><h2>{n_inv}</h2><p>Factures</p></div>
            <div class="stat"><h2>{n_quo}</h2><p>Devis</p></div>
        """

    rows = ""
    for doc in docs:
        data = doc["data"]
        name = data.get("full_name") or data.get("seller_name") or data.get("invoice_number") or "—"
        badge_class = doc["document_type"]
        rows += f"""
        <tr onclick="showDetail('{doc['id']}')" style="cursor:pointer">
            <td><span class="badge {badge_class}">{doc['document_type'].upper()}</span></td>
            <td>{name}</td>
            <td>{doc.get('filename') or '—'}</td>
            <td>{doc['created_at'][:19].replace('T', ' ')}</td>
        </tr>"""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: sans-serif; background: #f5f5f5; }}
            header {{ background: #1a1a2e; color: white; padding: 20px 40px; display: flex; justify-content: space-between; align-items: center; }}
            header h1 {{ font-size: 22px; }}
            header p {{ opacity: 0.7; font-size: 14px; margin-top: 4px; }}
            header .back {{ color:white; opacity:.6; text-decoration:none; font-size:13px; margin-right:16px; }}
            header .back:hover {{ opacity:1; }}
            .btn {{ background: {accent}; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; }}
            .btn:hover {{ opacity: 0.88; }}
            .container {{ padding: 30px 40px; }}
            .stats {{ display: flex; gap: 16px; margin-bottom: 24px; }}
            .stat {{ background: white; border-radius: 8px; padding: 16px 24px; flex: 1; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .stat h2 {{ font-size: 28px; color: {accent}; }}
            .stat p {{ color: #888; font-size: 13px; margin-top: 4px; }}
            .filters {{ margin-bottom: 16px; display: flex; gap: 8px; }}
            .filters a {{ padding: 6px 14px; border-radius: 20px; text-decoration: none; font-size: 13px; background: white; color: #555; border: 1px solid #ddd; }}
            .filters a:hover, .filters a.active {{ background: {accent}; color: white; border-color: {accent}; }}
            table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            th {{ background: #1a1a2e; color: white; padding: 12px 16px; text-align: left; font-size: 13px; }}
            td {{ padding: 12px 16px; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
            tr:hover td {{ background: #f0f4ff; }}
            .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
            .cv {{ background: #e8f4fd; color: #1a73e8; }}
            .invoice {{ background: #fef3e2; color: #f57c00; }}
            .quote {{ background: #e8f5e9; color: #2e7d32; }}
            .overlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:100; justify-content:center; align-items:center; }}
            .overlay.active {{ display:flex; }}
            .modal {{ background:white; border-radius:12px; padding:32px; width:500px; max-width:90%; }}
            .modal h2 {{ margin-bottom:20px; font-size:18px; }}
            .modal label {{ font-size:13px; color:#555; display:block; margin-bottom:6px; margin-top:16px; }}
            .modal input[type=file] {{ width:100%; border:1px solid #ddd; border-radius:8px; padding:10px; font-size:14px; }}
            .modal textarea {{ width:100%; border:1px solid #ddd; border-radius:8px; padding:10px; font-size:14px; height:140px; resize:vertical; }}
            .modal-footer {{ display:flex; justify-content:flex-end; gap:10px; margin-top:24px; }}
            .btn-cancel {{ background:#f0f0f0; color:#555; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; font-size:14px; }}
            .input-tab {{ flex:1; padding:10px; border-radius:8px; cursor:pointer; font-size:14px; font-weight:bold; transition: all 0.2s; }}
            .input-tab.active {{ background:#1a1a2e; color:white; border:2px solid #1a1a2e; }}
            .input-tab.inactive {{ background:white; color:#555; border:2px solid #ddd; }}
            #detail {{ display:none; position:fixed; top:0; right:0; width:42%; height:100%; background:white; box-shadow:-4px 0 16px rgba(0,0,0,0.15); overflow:auto; padding:28px; z-index:50; }}
            #detail h3 {{ margin-bottom:4px; font-size:17px; }}
            #detail .doc-type-badge {{ display:inline-block; margin-bottom:16px; }}
            #close {{ float:right; cursor:pointer; font-size:20px; color:#888; }}
            .detail-actions {{ display:flex; gap:8px; margin-top:20px; padding-top:16px; border-top:1px solid #eee; }}
            .btn-edit {{ background:#f0f4ff; color:#1a1a2e; border:1px solid #c0d0f0; padding:8px 16px; border-radius:8px; cursor:pointer; font-size:13px; font-weight:bold; }}
            .btn-save {{ background:#2e7d32; color:white; border:none; padding:8px 16px; border-radius:8px; cursor:pointer; font-size:13px; font-weight:bold; display:none; }}
            .btn-cancel-edit {{ background:#f0f0f0; color:#555; border:none; padding:8px 16px; border-radius:8px; cursor:pointer; font-size:13px; display:none; }}
            .btn-delete {{ background:#fdecea; color:#c0392b; border:1px solid #f5c6c2; padding:8px 16px; border-radius:8px; cursor:pointer; font-size:13px; font-weight:bold; margin-left:auto; }}
            /* ── Chatbot ── */
            #chat-btn {{ position:fixed; bottom:28px; right:28px; width:52px; height:52px; border-radius:50%; background:#1a1a2e; color:white; border:none; font-size:22px; cursor:pointer; box-shadow:0 4px 16px rgba(0,0,0,0.25); z-index:200; display:flex; align-items:center; justify-content:center; }}
            #chat-panel {{ display:none; position:fixed; bottom:90px; right:28px; width:380px; height:520px; background:white; border-radius:16px; box-shadow:0 8px 32px rgba(0,0,0,0.18); z-index:200; flex-direction:column; overflow:hidden; }}
            #chat-panel.open {{ display:flex; }}
            #chat-header {{ background:#1a1a2e; color:white; padding:14px 18px; font-size:14px; font-weight:bold; display:flex; justify-content:space-between; align-items:center; }}
            #chat-header span {{ opacity:.6; cursor:pointer; font-size:18px; }}
            #chat-messages {{ flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:10px; }}
            .msg {{ max-width:85%; padding:10px 14px; border-radius:12px; font-size:13px; line-height:1.5; }}
            .msg.bot {{ background:#f0f4ff; color:#1a1a2e; align-self:flex-start; border-bottom-left-radius:4px; }}
            .msg.user {{ background:#1a1a2e; color:white; align-self:flex-end; border-bottom-right-radius:4px; }}
            .msg.system {{ background:#fff3e0; color:#e65100; align-self:center; font-size:12px; border-radius:8px; }}
            .confirm-btns {{ display:flex; gap:8px; margin-top:8px; }}
            .confirm-btns button {{ padding:6px 14px; border-radius:8px; border:none; cursor:pointer; font-size:12px; font-weight:bold; }}
            .btn-confirm {{ background:#2e7d32; color:white; }}
            .btn-decline {{ background:#f0f0f0; color:#555; }}
            #chat-input-row {{ display:flex; gap:8px; padding:12px; border-top:1px solid #eee; }}
            #chat-input {{ flex:1; border:1px solid #ddd; border-radius:8px; padding:8px 12px; font-size:13px; outline:none; }}
            #chat-send {{ background:#1a1a2e; color:white; border:none; border-radius:8px; padding:8px 14px; cursor:pointer; font-size:16px; }}
            .typing {{ color:#aaa; font-size:12px; font-style:italic; }}
            .preview-list {{ display:flex; flex-direction:column; gap:6px; margin:10px 0 4px; }}
            .preview-card {{ display:flex; align-items:center; gap:10px; background:white; border-radius:8px; padding:8px 12px; border:1px solid #eee; font-size:12px; }}
            .preview-delete {{ border-left:3px solid #e53935; background:#fff5f5; }}
            .preview-update {{ border-left:3px solid #f57c00; background:#fff8f0; }}
            .preview-icon {{ font-size:18px; flex-shrink:0; }}
            .preview-card > div {{ flex:1; display:flex; flex-direction:column; gap:2px; }}
            .preview-card strong {{ font-size:13px; color:#1a1a2e; }}
            .preview-meta {{ color:#888; font-size:11px; }}
            .preview-meta code {{ background:#f0f0f0; padding:1px 4px; border-radius:3px; }}
            .preview-badge {{ font-size:10px; font-weight:bold; padding:2px 8px; border-radius:10px; flex-shrink:0; }}
            .preview-badge.del {{ background:#fdecea; color:#c0392b; }}
            .preview-badge.upd {{ background:#fff3e0; color:#e65100; }}
            .doc-cards-list {{ display:flex; flex-direction:column; gap:6px; padding:4px 0; max-width:85%; }}
            .doc-chat-card {{ display:flex; align-items:center; gap:10px; background:white; border:1px solid #e0e0e0; border-radius:10px; padding:10px 14px; cursor:pointer; transition:background .15s; }}
            .doc-chat-card:hover {{ background:#f0f4ff; border-color:#c0d0f0; }}
            .doc-card-icon {{ font-size:20px; flex-shrink:0; }}
            .doc-card-body {{ flex:1; display:flex; flex-direction:column; gap:2px; }}
            .doc-card-body strong {{ font-size:13px; color:#1a1a2e; }}
            .doc-card-meta {{ font-size:11px; color:#888; }}
            .doc-card-arrow {{ color:#aaa; font-size:18px; font-weight:bold; }}
            .field-group {{ margin-bottom:14px; }}
            .field-group label {{ font-size:11px; text-transform:uppercase; color:#999; font-weight:600; letter-spacing:.5px; display:block; margin-bottom:3px; }}
            .field-group .val {{ font-size:14px; color:#1a1a2e; }}
            .field-group .val.empty {{ color:#bbb; font-style:italic; }}
            .field-group input {{ width:100%; border:1px solid #ddd; border-radius:6px; padding:7px 10px; font-size:13px; }}
            .section-sep {{ font-size:12px; font-weight:700; color:#1a1a2e; text-transform:uppercase; letter-spacing:.5px; margin:20px 0 10px; padding-bottom:6px; border-bottom:2px solid #eee; }}
            .chip-list {{ display:flex; flex-wrap:wrap; gap:6px; }}
            .chip {{ background:#f0f4ff; color:#1a1a2e; border-radius:20px; padding:3px 10px; font-size:12px; }}
            .sub-card {{ background:#f9f9f9; border-radius:8px; padding:12px 14px; margin-bottom:8px; font-size:13px; }}
            .sub-card strong {{ display:block; margin-bottom:2px; }}
            .sub-card.edit-mode input {{ margin-bottom:6px; }}
        </style>
    </head>
    <body>
        <header>
            <div style="display:flex;align-items:center;gap:12px;">
                <a href="/home" class="back">← Accueil</a>
                <div>
                    <h1>{title}</h1>
                    <p>{subtitle}</p>
                </div>
            </div>
            <button class="btn" onclick="openModal()">+ Ajouter</button>
        </header>
        <div class="container">
            <div class="stats">{stats_html}</div>
            <div class="filters">{filters_html}</div>
            <table>
                <thead><tr><th>Type</th><th>Nom / Numéro</th><th>Fichier</th><th>Date</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>

        <!-- Modal -->
        <div class="overlay" id="overlay">
            <div class="modal">
                <h2>➕ Add a document</h2>
                <form action="/dashboard/upload" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="space" value="{space}">
                    <div style="display:flex;gap:12px;margin-bottom:20px;">
                        <button type="button" id="tab-file" class="input-tab active" onclick="switchInput('file')">📎 Upload a file</button>
                        <button type="button" id="tab-text" class="input-tab inactive" onclick="switchInput('text')">📝 Paste text</button>
                    </div>
                    <div id="input-file">
                        <label>Fichiers (PDF, DOCX, TXT) — sélection multiple possible</label>
                        <input type="file" name="files" accept=".pdf,.docx,.txt" multiple>
                    </div>
                    <div id="input-text" style="display:none;">
                        <label>Paste your document here</label>
                        <textarea name="text" placeholder="Paste your CV, invoice or quote here..."></textarea>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-cancel" onclick="closeModal()">Cancel</button>
                        <button type="submit" class="btn">Extract →</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Detail panel -->
        <div id="detail">
            <span id="close" onclick="closeDetail()">✕</span>
            <h3 id="detail-title">Document</h3>
            <div id="detail-badge" class="doc-type-badge"></div>
            <div id="detail-view"></div>
            <div id="detail-edit-form" style="display:none"></div>
            <div class="detail-actions">
                <button class="btn-edit" id="btn-edit" onclick="startEdit()">✏️ Modifier</button>
                <button class="btn-save" id="btn-save" onclick="saveEdit()">💾 Enregistrer</button>
                <button class="btn-cancel-edit" id="btn-cancel-edit" onclick="cancelEdit()">Annuler</button>
                <button class="btn-delete" onclick="deleteDoc()">🗑️ Supprimer</button>
            </div>
        </div>

        <!-- Chatbot -->
        <button id="chat-btn" onclick="toggleChat()" title="Assistant">💬</button>
        <div id="chat-panel">
            <div id="chat-header">
                🤖 Assistant Dashboard
                <span onclick="toggleChat()">✕</span>
            </div>
            <div id="chat-messages">
                <div class="msg bot">{chat_intro}</div>
            </div>
            <div id="chat-input-row">
                <input id="chat-input" type="text" placeholder="Posez votre question..." onkeydown="if(event.key==='Enter') sendChat()" />
                <button id="chat-send" onclick="sendChat()">➤</button>
            </div>
        </div>

        <script>
            const docs = {docs_json};

            function openModal() {{ document.getElementById('overlay').classList.add('active'); }}
            function closeModal() {{ document.getElementById('overlay').classList.remove('active'); }}

            function switchInput(type) {{
                document.getElementById('input-file').style.display = type === 'file' ? 'block' : 'none';
                document.getElementById('input-text').style.display = type === 'text' ? 'block' : 'none';
                document.getElementById('tab-file').className = 'input-tab ' + (type === 'file' ? 'active' : 'inactive');
                document.getElementById('tab-text').className = 'input-tab ' + (type === 'text' ? 'active' : 'inactive');
            }}

            let currentId = null;
            let currentDoc = null;

            const LABELS = {{
                full_name:'Nom complet', email:'Email', phone:'Téléphone', location:'Localisation',
                linkedin_url:'LinkedIn', summary:'Résumé', skills:'Compétences', languages:'Langues',
                invoice_number:'N° facture', invoice_date:'Date', due_date:'Échéance', currency:'Devise',
                seller_name:'Vendeur', seller_address:'Adresse vendeur', seller_vat_number:'N° TVA',
                buyer_name:'Acheteur', buyer_address:'Adresse acheteur',
                total_ht:'Total HT', total_vat:'TVA', total_ttc:'Total TTC', payment_method:'Paiement',
                notes:'Notes', quote_number:'N° devis', quote_date:'Date', valid_until:'Valide jusqu\u2019au',
                seller_email:'Email vendeur', seller_phone:'Tél vendeur',
                client_name:'Client', client_address:'Adresse client',
                discount_total:'Remise', payment_terms:'Conditions paiement', delivery_delay:'Délai livraison'
            }};

            function field(key, val, edit=false) {{
                const label = LABELS[key] || key;
                if (edit) {{
                    return `<div class="field-group"><label>${{label}}</label>
                        <input type="text" name="${{key}}" value="${{val ?? ''}}" /></div>`;
                }}
                const display = (val === null || val === undefined || val === '')
                    ? `<span class="val empty">—</span>`
                    : `<span class="val">${{val}}</span>`;
                return `<div class="field-group"><label>${{label}}</label>${{display}}</div>`;
            }}

            function chips(key, arr, edit=false) {{
                const label = LABELS[key] || key;
                if (edit) {{
                    return `<div class="field-group"><label>${{label}}</label>
                        <input type="text" name="${{key}}" value="${{(arr||[]).join(', ')}}" /></div>`;
                }}
                const chips = (arr||[]).map(s=>`<span class="chip">${{s}}</span>`).join('');
                return `<div class="field-group"><label>${{label}}</label>
                    <div class="chip-list">${{chips || '<span class="val empty">—</span>'}}</div></div>`;
            }}

            function renderCV(data, edit=false) {{
                let html = field('full_name', data.full_name, edit)
                    + field('email', data.email, edit)
                    + field('phone', data.phone, edit)
                    + field('location', data.location, edit)
                    + field('linkedin_url', data.linkedin_url, edit)
                    + field('summary', data.summary, edit)
                    + chips('skills', data.skills, edit)
                    + chips('languages', data.languages, edit);

                if (!edit && data.experiences && data.experiences.length) {{
                    html += `<div class="section-sep">Expériences</div>`;
                    data.experiences.forEach(e => {{
                        html += `<div class="sub-card">
                            <strong>${{e.position || '—'}} — ${{e.company}}</strong>
                            <span style="color:#888;font-size:12px">${{e.start_date}} - ${{e.end_date || 'en poste'}}</span>
                            ${{e.description ? `<p style="margin-top:6px;color:#555;font-size:12px">${{e.description}}</p>` : ''}}
                        </div>`;
                    }});
                }}
                if (!edit && data.education && data.education.length) {{
                    html += `<div class="section-sep">Formation</div>`;
                    data.education.forEach(e => {{
                        html += `<div class="sub-card">
                            <strong>${{e.institution}}</strong>
                            ${{e.degree ? `${{e.degree}}${{e.field_of_study ? ' — '+e.field_of_study : ''}}` : ''}}
                            ${{e.graduation_year ? `<span style="color:#888;font-size:12px;display:block">${{e.graduation_year}}</span>` : ''}}
                        </div>`;
                    }});
                }}
                return html;
            }}

            function renderInvoice(data, edit=false) {{
                let html = field('invoice_number', data.invoice_number, edit)
                    + field('invoice_date', data.invoice_date, edit)
                    + field('due_date', data.due_date, edit)
                    + field('currency', data.currency, edit);
                html += `<div class="section-sep">Vendeur</div>`
                    + field('seller_name', data.seller_name, edit)
                    + field('seller_address', data.seller_address, edit)
                    + field('seller_vat_number', data.seller_vat_number, edit);
                html += `<div class="section-sep">Acheteur</div>`
                    + field('buyer_name', data.buyer_name, edit)
                    + field('buyer_address', data.buyer_address, edit);
                html += `<div class="section-sep">Totaux</div>`
                    + field('total_ht', data.total_ht, edit)
                    + field('total_vat', data.total_vat, edit)
                    + field('total_ttc', data.total_ttc, edit)
                    + field('payment_method', data.payment_method, edit)
                    + field('notes', data.notes, edit);
                return html;
            }}

            function renderQuote(data, edit=false) {{
                let html = field('quote_number', data.quote_number, edit)
                    + field('quote_date', data.quote_date, edit)
                    + field('valid_until', data.valid_until, edit)
                    + field('currency', data.currency, edit);
                html += `<div class="section-sep">Prestataire</div>`
                    + field('seller_name', data.seller_name, edit)
                    + field('seller_address', data.seller_address, edit)
                    + field('seller_email', data.seller_email, edit)
                    + field('seller_phone', data.seller_phone, edit);
                html += `<div class="section-sep">Client</div>`
                    + field('client_name', data.client_name, edit)
                    + field('client_address', data.client_address, edit);
                html += `<div class="section-sep">Totaux</div>`
                    + field('total_ht', data.total_ht, edit)
                    + field('total_vat', data.total_vat, edit)
                    + field('total_ttc', data.total_ttc, edit)
                    + field('payment_terms', data.payment_terms, edit)
                    + field('delivery_delay', data.delivery_delay, edit)
                    + field('notes', data.notes, edit);
                return html;
            }}

            function renderDoc(doc, edit=false) {{
                if (doc.document_type === 'cv') return renderCV(doc.data, edit);
                if (doc.document_type === 'invoice') return renderInvoice(doc.data, edit);
                return renderQuote(doc.data, edit);
            }}

            function showDetail(id) {{
                const doc = docs.find(d => d.id === id);
                if (!doc) return;
                currentId = id;
                currentDoc = doc;
                document.getElementById('detail-title').textContent =
                    doc.data.full_name || doc.data.invoice_number || doc.data.quote_number || 'Document';
                const badgeEl = document.getElementById('detail-badge');
                badgeEl.innerHTML = `<span class="badge ${{doc.document_type}}">${{doc.document_type.toUpperCase()}}</span>`;
                document.getElementById('detail-view').innerHTML = renderDoc(doc);
                document.getElementById('detail-view').style.display = 'block';
                document.getElementById('detail-edit-form').style.display = 'none';
                document.getElementById('btn-edit').style.display = 'inline-block';
                document.getElementById('btn-save').style.display = 'none';
                document.getElementById('btn-cancel-edit').style.display = 'none';
                document.getElementById('detail').style.display = 'block';
            }}

            function closeDetail() {{
                document.getElementById('detail').style.display = 'none';
            }}

            function startEdit() {{
                document.getElementById('detail-view').style.display = 'none';
                document.getElementById('detail-edit-form').innerHTML = renderDoc(currentDoc, true);
                document.getElementById('detail-edit-form').style.display = 'block';
                document.getElementById('btn-edit').style.display = 'none';
                document.getElementById('btn-save').style.display = 'inline-block';
                document.getElementById('btn-cancel-edit').style.display = 'inline-block';
            }}

            function cancelEdit() {{
                document.getElementById('detail-view').style.display = 'block';
                document.getElementById('detail-edit-form').style.display = 'none';
                document.getElementById('btn-edit').style.display = 'inline-block';
                document.getElementById('btn-save').style.display = 'none';
                document.getElementById('btn-cancel-edit').style.display = 'none';
            }}

            async function saveEdit() {{
                const form = document.getElementById('detail-edit-form');
                const inputs = form.querySelectorAll('input[name]');
                const updated = JSON.parse(JSON.stringify(currentDoc.data));
                inputs.forEach(inp => {{
                    const key = inp.name;
                    if (key === 'skills' || key === 'languages') {{
                        updated[key] = inp.value ? inp.value.split(',').map(s=>s.trim()).filter(Boolean) : [];
                    }} else {{
                        updated[key] = inp.value || null;
                    }}
                }});
                await fetch('/dashboard/documents/' + currentId, {{
                    method: 'PUT',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(updated)
                }});
                location.reload();
            }}

            async function deleteDoc() {{
                if (!confirm('Supprimer ce document ?')) return;
                await fetch('/dashboard/documents/' + currentId, {{ method: 'DELETE' }});
                location.reload();
            }}

            // ── Chatbot ──────────────────────────────────────────────────
            let chatHistory = [];
            let pendingAction = null;

            function toggleChat() {{
                document.getElementById('chat-panel').classList.toggle('open');
                if (document.getElementById('chat-panel').classList.contains('open'))
                    document.getElementById('chat-input').focus();
            }}

            function appendMsg(text, role, extra='') {{
                const div = document.createElement('div');
                div.className = 'msg ' + role;
                div.innerHTML = text.replace(/\\n/g, '<br>') + extra;
                document.getElementById('chat-messages').appendChild(div);
                document.getElementById('chat-messages').scrollTop = 99999;
                return div;
            }}

            function appendDocCards(ids) {{
                const container = document.createElement('div');
                container.className = 'doc-cards-list';
                ids.forEach(id => {{
                    const d = docs.find(x => x.id === id);
                    if (!d) return;
                    const name = d.data.full_name || d.data.invoice_number || d.data.quote_number || d.data.seller_name || '—';
                    const icon = {{cv:'👤', invoice:'🧾', quote:'📋'}}[d.document_type] || '📄';
                    const label = {{cv:'CV', invoice:'Facture', quote:'Devis'}}[d.document_type] || d.document_type;
                    const card = document.createElement('div');
                    card.className = 'doc-chat-card';
                    card.innerHTML = `<span class="doc-card-icon">${{icon}}</span>
                        <div class="doc-card-body"><strong>${{name}}</strong>
                        <span class="doc-card-meta">${{label}} · ${{d.created_at.slice(0,10)}}${{d.filename ? ' · '+d.filename : ''}}</span></div>
                        <span class="doc-card-arrow">›</span>`;
                    card.onclick = () => showDetail(id);
                    container.appendChild(card);
                }});
                document.getElementById('chat-messages').appendChild(container);
                document.getElementById('chat-messages').scrollTop = 99999;
            }}

            const TYPE_ICONS = {{ cv:'👤', invoice:'🧾', quote:'📋' }};
            const TYPE_LABELS = {{ cv:'CV', invoice:'Facture', quote:'Devis' }};

            function buildPreview(action) {{
                const p = action.params || {{}};
                const t = action.type;

                if ((t === 'delete_document' || t === 'delete_documents')) {{
                    const ids = t === 'delete_document' ? [p.doc_id] : (p.doc_ids || []);
                    const items = ids.map(id => {{
                        const d = docs.find(x => x.id === id);
                        if (!d) return '';
                        const name = d.data.full_name || d.data.invoice_number || d.data.quote_number || d.data.seller_name || '—';
                        const icon = TYPE_ICONS[d.document_type] || '📄';
                        const label = TYPE_LABELS[d.document_type] || d.document_type;
                        return `<div class="preview-card preview-delete">
                            <span class="preview-icon">${{icon}}</span>
                            <div><strong>${{name}}</strong><span class="preview-meta">${{label}} · ${{d.created_at.slice(0,10)}}</span></div>
                            <span class="preview-badge del">Suppression</span>
                        </div>`;
                    }}).join('');
                    return items || `<div class="preview-card preview-delete"><span class="preview-icon">🗑️</span><div><strong>${{action.description}}</strong></div></div>`;
                }}

                if (t === 'update_field') {{
                    const d = docs.find(x => x.id === p.doc_id);
                    const name = d ? (d.data.full_name || d.data.invoice_number || d.data.seller_name || '—') : (p.doc_name || '—');
                    return `<div class="preview-card preview-update">
                        <span class="preview-icon">✏️</span>
                        <div><strong>${{name}}</strong>
                        <span class="preview-meta">Champ : <code>${{p.field}}</code> → <code>${{p.value}}</code></span></div>
                        <span class="preview-badge upd">Modification</span>
                    </div>`;
                }}

                return `<div class="preview-card"><span class="preview-icon">⚙️</span><div><strong>${{action.description}}</strong></div></div>`;
            }}

            function appendConfirm(action) {{
                const div = document.createElement('div');
                div.className = 'msg bot';
                div.innerHTML = `
                    <strong>Je vais effectuer l'action suivante :</strong>
                    <div class="preview-list">${{buildPreview(action)}}</div>
                    <div class="confirm-btns">
                        <button class="btn-confirm" onclick="confirmAction()">✅ Confirmer</button>
                        <button class="btn-decline" onclick="declineAction()">❌ Annuler</button>
                    </div>`;
                document.getElementById('chat-messages').appendChild(div);
                document.getElementById('chat-messages').scrollTop = 99999;
            }}

            async function sendChat() {{
                const input = document.getElementById('chat-input');
                const msg = input.value.trim();
                if (!msg) return;
                input.value = '';
                appendMsg(msg, 'user');
                chatHistory.push({{ role: 'user', content: msg }});

                const typing = appendMsg('<span class="typing">…</span>', 'bot');

                try {{
                    const res = await fetch('/dashboard/chat', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ message: msg, history: chatHistory.slice(-10) }})
                    }});
                    const data = await res.json();
                    typing.remove();

                    appendMsg(data.message || '…', 'bot');
                    chatHistory.push({{ role: 'assistant', content: data.message || '' }});

                    if (data.action && data.action.type === 'show_document') {{
                        showDetail(data.action.params.doc_id);
                    }} else if (data.action && data.action.type === 'show_documents') {{
                        appendDocCards(data.action.params.doc_ids);
                    }} else if (data.action && data.requires_confirmation) {{
                        pendingAction = data.action;
                        appendConfirm(data.action);
                    }} else if (data.action) {{
                        await executeAction(data.action);
                    }}
                }} catch(e) {{
                    typing.remove();
                    appendMsg('Une erreur est survenue, réessayez.', 'system');
                }}
            }}

            async function confirmAction() {{
                if (!pendingAction) return;
                const action = pendingAction;
                pendingAction = null;
                document.querySelectorAll('.confirm-btns').forEach(el => el.remove());
                appendMsg('Action confirmée, exécution en cours…', 'system');
                await executeAction(action);
            }}

            function declineAction() {{
                pendingAction = null;
                document.querySelectorAll('.confirm-btns').forEach(el => el.remove());
                appendMsg('Action annulée.', 'system');
            }}

            async function executeAction(action) {{
                try {{
                    const res = await fetch('/dashboard/execute', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ action }})
                    }});
                    const data = await res.json();
                    appendMsg(data.message || 'Fait !', 'system');
                    if (data.reload) setTimeout(() => location.reload(), 1200);
                }} catch(e) {{
                    appendMsg("Erreur lors de l'exécution.", 'system');
                }}
            }}
        </script>
    </body>
    </html>
    """


@router.get("/dashboard/hr", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_hr(type: str = Query(None)):
    return HTMLResponse(content=await render_dashboard("hr", type))


@router.get("/dashboard/finance", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_finance(type: str = Query(None)):
    return HTMLResponse(content=await render_dashboard("finance", type))