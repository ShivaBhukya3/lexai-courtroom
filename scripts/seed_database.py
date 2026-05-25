"""Seed the database with sample cases."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def seed():
    from database.connection import init_db, SessionLocal
    from database import crud

    print("\n" + "=" * 50)
    print("  LexAI — Database Seeder")
    print("=" * 50)

    init_db()
    db = SessionLocal()

    cases_dir = Path(__file__).parent.parent / "data" / "cases" / "sample_cases"
    seeded = 0

    for case_dir in cases_dir.iterdir():
        meta_path = case_dir / "case_metadata.json"
        if not meta_path.exists():
            continue

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        existing = crud.get_case(db, meta["case_id"])
        if existing:
            print(f"  [~] {meta['case_id']} already exists — skipping")
            continue

        case = crud.create_case(db, meta)
        print(f"  [✓] Created case: {case.id} — {meta.get('case_type','')}")
        seeded += 1

    db.close()
    print(f"\n  {seeded} cases seeded successfully!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    seed()
