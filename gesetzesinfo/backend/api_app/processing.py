import os
import sqlite3
from django.conf import settings
from django.db import transaction
import faiss

from .models import Law, EmbeddedLaw, OpenLegalDataLawTest, get_law_model


def populate_law_db():
    if not settings.USE_TEST_DB:
        print("Test database population skipped: USE_TEST_DB is False")
        return

    # Use the correct path for the test database and FAISS index
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_db_path = os.path.join(backend_dir, 'law_db.sqlite3')
    faiss_db_path = os.path.join(backend_dir, 'law_vector_db.faiss')
    
    if not os.path.exists(test_db_path):
        print(f"Test database not found at {test_db_path}")
        return

    if not os.path.exists(faiss_db_path):
        print(f"FAISS index not found at {faiss_db_path}")
        return

    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()

    # Fetch all columns from the embedded_laws table
    cursor.execute("SELECT law_id, book_code, title, text, source_url, embedding FROM embedded_laws")
    embedded_laws = [dict(row) for row in cursor.fetchall()]

    # Clear existing data
    EmbeddedLaw.objects.all().delete()

    # Bulk create new objects
    EmbeddedLaw.objects.bulk_create([
        EmbeddedLaw(
            law_id=law['law_id'],
            book_code=law['book_code'],
            title=law['title'],
            text=law['text'],
            source_url=law['source_url'],

            text_reduced=law['text'][:EmbeddedLaw.reduced_text_length],
            embedding_text=law['text'],
            embedding_base=law['embedding'],
            embedding_optimized=law['embedding'] 
        ) for law in embedded_laws
    ])

    conn.close()
    print(f"Populated {len(embedded_laws)} laws into EmbeddedLaw")

    # Load the FAISS index
    index = faiss.read_index(faiss_db_path)
    print(f"Loaded FAISS index with {index.ntotal} vectors")

