"""Ingestează un document în RAG: load -> chunk -> extract -> store."""

import sys

from extraction.pipeline import process
from db.database import transaction
from db.repository import DocumentRepository


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "data/cec_comisioane.pdf"

    # reset: ștergem documentele existente ca să nu dublăm la re-rulare
    with transaction() as db:
        n = DocumentRepository(db).delete_all()
        if n:
            print(f"Șterse {n} documente existente.")

    print(f"Procesez {path} ...")
    rez = process(path)
    print("Gata:")
    for k, v in rez.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()