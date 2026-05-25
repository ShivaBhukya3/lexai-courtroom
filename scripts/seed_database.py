"""Seed the database with realistic Indian legal cases."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

SAMPLE_CASES = [
    {
        "case_name": "State of Maharashtra v. Arjun Ramesh Pawar",
        "case_type": "Criminal",
        "sub_type": "Murder",
        "court": "Sessions Court, Pune",
        "charges": ["IPC Section 302 — Murder", "IPC Section 201 — Causing disappearance of evidence"],
        "plaintiff_name": "State of Maharashtra",
        "defendant_name": "Arjun Ramesh Pawar",
        "status": "Active",
        "judge": "Hon. Justice R.K. Sharma",
        "filing_date": "2024-08-12",
        "next_hearing": "2026-06-15",
    },
    {
        "case_name": "Priya Kapoor v. Vikram Kapoor & Others",
        "case_type": "Criminal",
        "sub_type": "Dowry & Domestic Violence",
        "court": "Additional Sessions Court, Delhi",
        "charges": ["IPC Section 498A — Cruelty by husband/relatives", "IPC Section 304B — Dowry death", "Dowry Prohibition Act 1961"],
        "plaintiff_name": "Priya Kapoor",
        "defendant_name": "Vikram Kapoor & Family",
        "status": "Active",
        "judge": "Hon. Justice Sunita Mehta",
        "filing_date": "2024-11-03",
        "next_hearing": "2026-06-20",
    },
    {
        "case_name": "CBI v. Rajendra Kumar Sinha",
        "case_type": "Criminal",
        "sub_type": "Financial Fraud",
        "court": "Special CBI Court, Mumbai",
        "charges": ["IPC Section 420 — Cheating", "IPC Section 468 — Forgery for cheating", "IPC Section 471 — Using forged documents", "Prevention of Corruption Act 1988 — Section 7"],
        "plaintiff_name": "Central Bureau of Investigation",
        "defendant_name": "Rajendra Kumar Sinha",
        "status": "Active",
        "judge": "Hon. Justice P.D. Vora",
        "filing_date": "2024-05-18",
        "next_hearing": "2026-07-02",
    },
    {
        "case_name": "Ramesh Baburao Patil v. Suresh Govind Patil",
        "case_type": "Civil",
        "sub_type": "Property Dispute",
        "court": "Civil Judge Senior Division, Nashik",
        "charges": ["Recovery of possession of agricultural land", "Declaration of title", "Permanent injunction"],
        "plaintiff_name": "Ramesh Baburao Patil",
        "defendant_name": "Suresh Govind Patil",
        "status": "Active",
        "judge": "Hon. Justice Priya Deshmukh",
        "filing_date": "2024-01-15",
        "next_hearing": "2026-06-18",
    },
    {
        "case_name": "InfraCore Ltd. v. Bharat Steel Works Pvt. Ltd.",
        "case_type": "Corporate",
        "sub_type": "Commercial Dispute",
        "court": "National Company Law Tribunal, Bengaluru",
        "charges": ["Breach of contract — ₹4.2 crore supply agreement", "Companies Act 2013 — Section 241 (Oppression)", "Insolvency and Bankruptcy Code 2016 — Section 9"],
        "plaintiff_name": "InfraCore Ltd.",
        "defendant_name": "Bharat Steel Works Pvt. Ltd.",
        "status": "Active",
        "judge": "Hon. Member Justice K.L. Rathi",
        "filing_date": "2025-02-10",
        "next_hearing": "2026-06-25",
    },
    {
        "case_name": "State of Rajasthan v. Mohammad Aslam Khan",
        "case_type": "Criminal",
        "sub_type": "Robbery & Assault",
        "court": "Sessions Court, Jaipur",
        "charges": ["IPC Section 392 — Robbery", "IPC Section 394 — Voluntarily causing hurt in robbery", "IPC Section 397 — Robbery with deadly weapon"],
        "plaintiff_name": "State of Rajasthan",
        "defendant_name": "Mohammad Aslam Khan",
        "status": "Active",
        "judge": "Hon. Justice A.S. Gupta",
        "filing_date": "2025-01-22",
        "next_hearing": "2026-07-10",
    },
    {
        "case_name": "Sunita Devi v. Haryana State & Others",
        "case_type": "Civil",
        "sub_type": "Writ Petition — Wrongful Termination",
        "court": "Punjab & Haryana High Court, Chandigarh",
        "charges": ["Article 226 — Writ of Mandamus", "Industrial Disputes Act 1947 — Section 25F", "Wrongful termination without due process"],
        "plaintiff_name": "Sunita Devi",
        "defendant_name": "State of Haryana & Director of Education",
        "status": "Active",
        "judge": "Hon. Justice T.P. Singh",
        "filing_date": "2025-03-05",
        "next_hearing": "2026-06-30",
    },
    {
        "case_name": "Ananya Biotech Pvt. Ltd. v. Ravi Shankar Reddy",
        "case_type": "Corporate",
        "sub_type": "IP Theft & Trade Secret",
        "court": "Commercial Court, Hyderabad",
        "charges": ["IPC Section 408 — Criminal breach of trust by employee", "IPC Section 420 — Cheating", "Information Technology Act 2000 — Section 43A", "Trade Secrets misappropriation"],
        "plaintiff_name": "Ananya Biotech Pvt. Ltd.",
        "defendant_name": "Ravi Shankar Reddy",
        "status": "Active",
        "judge": "Hon. Justice M.S. Rao",
        "filing_date": "2025-04-14",
        "next_hearing": "2026-07-18",
    },
]


def seed():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    from database.connection import init_db, SessionLocal
    from database import crud

    print("\n" + "=" * 60)
    print("  LexAI — Database Seeder")
    print("=" * 60)

    init_db()
    db = SessionLocal()

    seeded = 0
    skipped = 0

    for case_data in SAMPLE_CASES:
        # Generate a deterministic case_id from the case name
        import hashlib
        name_hash = hashlib.md5(case_data["case_name"].encode()).hexdigest()[:8].upper()
        case_id = f"CASE-{name_hash}"
        case_data["case_id"] = case_id

        existing = crud.get_case(db, case_id)
        if existing:
            print(f"  [~] {case_id} already exists — skipping")
            skipped += 1
            continue

        case = crud.create_case(db, case_data)
        print(f"  [✓] {case.id} — {case_data['case_name'][:55]}")
        seeded += 1

    db.close()
    print(f"\n  Seeded: {seeded}  |  Skipped: {skipped}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    seed()
