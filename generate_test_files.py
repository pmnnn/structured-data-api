"""
Generate 30 random test files (CV, invoice, quote) in docx, txt, or pdf format.
Output directory: test_files/
"""
import os
import random
from pathlib import Path

random.seed(99)
OUTPUT_DIR = Path("test_files")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Sample data pools ────────────────────────────────────────────────────────

FIRST_NAMES = ["Alice", "Thomas", "Camille", "Julien", "Sophie", "Maxime",
               "Emma", "Lucas", "Léa", "Antoine", "Chloé", "Nicolas"]
LAST_NAMES  = ["Martin", "Bernard", "Dupont", "Moreau", "Laurent", "Simon",
               "Michel", "Lefebvre", "Garcia", "Roux", "David", "Petit"]
COMPANIES   = ["Airbus", "Thales", "Capgemini", "Dassault Systèmes", "Orange",
               "BNP Paribas", "L'Oréal", "Safran", "Renault", "Société Générale"]
CITIES      = ["Paris", "Lyon", "Toulouse", "Bordeaux", "Nantes", "Marseille",
               "Strasbourg", "Rennes", "Lille", "Montpellier"]

def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def rand_company():
    return random.choice(COMPANIES)

def rand_city():
    return random.choice(CITIES)

def rand_invoice_number():
    return f"FAC-2025-{random.randint(1000, 9999)}"

def rand_quote_number():
    return f"DEV-2025-{random.randint(100, 999)}"

def rand_date():
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return f"2025-{m:02d}-{d:02d}"

def rand_amount():
    return round(random.uniform(500, 10000), 2)

# ── Content generators ────────────────────────────────────────────────────────

def cv_text(name=None):
    name = name or rand_name()
    city = rand_city()
    email = name.lower().replace(" ", ".") + "@email.fr"
    company1, company2 = rand_company(), rand_company()
    return f"""CV - {name}

Email : {email}
Téléphone : 06 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}
Localisation : {city}, France

PROFIL
Ingénieur logiciel avec 5 ans d'expérience en développement backend et cloud. \
Passionné par les systèmes distribués et l'automatisation.

EXPÉRIENCE PROFESSIONNELLE

{company1} — Ingénieur Logiciel Senior  (2022 – présent)  {city}
  Développement de microservices en Python et Go. Mise en place de pipelines CI/CD.
  Technologies : Kubernetes, Docker, AWS, PostgreSQL.

{company2} — Développeur Backend  (2019 – 2022)  Paris
  Conception d'APIs REST, intégration de services tiers, optimisation SQL.
  Technologies : FastAPI, Django, Redis, MySQL.

FORMATION

École Polytechnique — Master Informatique  (2019)  Palaiseau
Licence Sciences et Technologies — Université Paris-Saclay  (2017)

COMPÉTENCES TECHNIQUES
Langages : Python, Go, Java, SQL, Bash
Cloud/DevOps : AWS, Azure, Docker, Kubernetes, Terraform, CI/CD
Bases de données : PostgreSQL, MySQL, MongoDB, Redis
Frameworks : FastAPI, Django, Spring Boot

LANGUES
Français (natif), Anglais (courant), Espagnol (notions)

CENTRES D'INTÉRÊT
Escalade, photographie, contributions open-source
"""

def invoice_text():
    seller = rand_company()
    buyer  = rand_company()
    num    = rand_invoice_number()
    date   = rand_date()
    city   = rand_city()
    ht     = rand_amount()
    vat    = round(ht * 0.20, 2)
    ttc    = round(ht + vat, 2)
    return f"""FACTURE

Numéro de facture : {num}
Date de facturation : {date}
Date d'échéance : 2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}

VENDEUR
{seller}
12 avenue de la République, {city}, France
TVA : FR{random.randint(10,99)}{random.randint(100000000,999999999)}

ACHETEUR
{buyer}
8 rue du Commerce, Paris 75011, France

PRESTATIONS
----------------------------------------------------------
Description                          Qté   PU HT    Total HT
Développement logiciel personnalisé  1     {ht:.2f}  {ht:.2f}
Maintenance mensuelle                2     500.00   1000.00
Formation utilisateurs               1     800.00    800.00
----------------------------------------------------------
Total HT       : {ht:.2f} €
TVA 20%        : {vat:.2f} €
Total TTC      : {ttc:.2f} €

Mode de paiement : Virement bancaire
IBAN : FR76 3000 1007 9412 3456 7890 185
"""

def quote_text():
    seller = rand_company()
    client = rand_company()
    num    = rand_quote_number()
    date   = rand_date()
    city   = rand_city()
    ht     = rand_amount()
    vat    = round(ht * 0.20, 2)
    ttc    = round(ht + vat, 2)
    return f"""DEVIS

Numéro de devis : {num}
Date d'émission : {date}
Valable jusqu'au : 2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}

PRESTATAIRE
{seller}
45 boulevard Haussmann, {city}, France
contact@{seller.lower().replace(' ', '')}.fr — +33 1 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}

CLIENT
{client}
27 rue Lafayette, Paris 75009, France

DÉTAIL DES PRESTATIONS
----------------------------------------------------------
Description                          Qté   PU HT    Total HT
Audit et conseil stratégique         3     {round(ht/3,2):.2f}   {ht:.2f}
Développement application mobile     1     2500.00  2500.00
Intégration API et tests             1     1200.00  1200.00
----------------------------------------------------------
Total HT        : {ht:.2f} €
TVA 20%         : {vat:.2f} €
Total TTC       : {ttc:.2f} €

Délai de réalisation : 6 semaines
Conditions de paiement : 30% à la commande, solde à la livraison

Signature client : ___________________
"""

# ── File writers ──────────────────────────────────────────────────────────────

def write_txt(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

def write_docx(path: Path, content: str):
    from docx import Document
    doc = Document()
    for line in content.strip().split("\n"):
        doc.add_paragraph(line)
    doc.save(path)

def write_pdf(path: Path, content: str):
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    # Insert text with a simple monospace font, wrapping manually
    y = 50
    for line in content.strip().split("\n"):
        if y > 780:
            page = doc.new_page()
            y = 50
        page.insert_text((50, y), line, fontsize=10, fontname="helv")
        y += 14
    doc.save(path)
    doc.close()

# ── Main generation ───────────────────────────────────────────────────────────

TYPES  = ["cv", "invoice", "quote"]
EXTS   = ["txt", "docx", "pdf"]

generators = {
    "cv":      cv_text,
    "invoice": invoice_text,
    "quote":   quote_text,
}
writers = {
    "txt":  write_txt,
    "docx": write_docx,
    "pdf":  write_pdf,
}

CV_FILENAME_PATTERNS = [
    lambda fn, ln: f"CV_{fn}_{ln}",
    lambda fn, ln: f"cv_{fn.lower()}_{ln.lower()}",
    lambda fn, ln: f"CV_{ln.upper()}_{fn}",
    lambda fn, ln: f"MonCV_{fn}",
    lambda fn, ln: f"CV_{ln}_2025",
    lambda fn, ln: f"curriculum_vitae_{fn.lower()}",
    lambda fn, ln: f"CV {fn} {ln}",
    lambda fn, ln: f"{fn}_{ln}_CV",
    lambda fn, ln: f"cv_final_{ln.lower()}",
    lambda fn, ln: f"CV_candidature_{fn}",
]

INVOICE_FILENAME_PATTERNS = [
    lambda s, n: f"Facture_{n}",
    lambda s, n: f"facture_{s.lower().replace(' ', '_')}_{n}",
    lambda s, n: f"FACTURE-{n}",
    lambda s, n: f"Facture {s} 2025",
    lambda s, n: f"fact_{n}_2025",
    lambda s, n: f"Facture_{s.replace(' ', '')}",
    lambda s, n: f"invoice_{n}",
    lambda s, n: f"Facture-{n}-avril2025",
    lambda s, n: f"{s.replace(' ', '_')}_facture",
    lambda s, n: f"FAC_{n}",
]

QUOTE_FILENAME_PATTERNS = [
    lambda s, n: f"Devis_{n}",
    lambda s, n: f"devis_{s.lower().replace(' ', '_')}",
    lambda s, n: f"Devis {s} 2025",
    lambda s, n: f"DEVIS-{n}",
    lambda s, n: f"devis_client_{n}",
    lambda s, n: f"Proposition_{s.replace(' ', '')}",
    lambda s, n: f"devis_{n}_final",
    lambda s, n: f"Devis-{n}-2025",
    lambda s, n: f"cotation_{s.lower().replace(' ', '_')}",
    lambda s, n: f"DEV_{n}",
]

def sanitize(name: str) -> str:
    """Remove characters that are invalid in filenames."""
    for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', "'", "'"]:
        name = name.replace(ch, '')
    return name.strip()

generated = []
for i in range(1, 31):
    doc_type = random.choice(TYPES)
    ext      = random.choice(EXTS)

    if doc_type == "cv":
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        content  = cv_text(f"{fn} {ln}")
        raw_name = random.choice(CV_FILENAME_PATTERNS)(fn, ln)
    elif doc_type == "invoice":
        seller = rand_company()
        num    = rand_invoice_number()
        content  = invoice_text()
        raw_name = random.choice(INVOICE_FILENAME_PATTERNS)(seller, num)
    else:
        seller = rand_company()
        num    = rand_quote_number()
        content  = quote_text()
        raw_name = random.choice(QUOTE_FILENAME_PATTERNS)(seller, num)

    filename = f"{sanitize(raw_name)}.{ext}"
    path     = OUTPUT_DIR / filename
    writers[ext](path, content)
    generated.append(filename)
    print(f"[{i:02d}] {filename}")

print(f"\n✓ {len(generated)} files generated in ./{OUTPUT_DIR}/")
