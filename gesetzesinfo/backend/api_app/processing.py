import os
import sqlite3
from django.conf import settings
from django.db import transaction

from .models import Law, EmbeddedLaw, OpenLegalDataLawTest, get_law_model



def old_to_law_model():
    '''
    This function is used to convert the OpenLegalData law model to the general law model.
    This is done, so we can define our own model however we want and making sure we can use data from different sources.
    '''
    # Get the old law model, handling test and real db
    old_law_model = get_law_model()

    #Clear existing data in the Law model
    Law.objects.all().delete()

    # Fetch all OpenLegalDataLaw objects
    open_legal_laws = old_law_model.objects.all()

    # Bulk create new Law objects
    Law.objects.bulk_create([
        Law(
            book_code=law.book_code,
            title=law.title,
            text=law.text,
            source_url='https://de.openlegaldata.io/'  # Assuming source_url is not available in OpenLegalDataLaw
        ) for law in open_legal_laws
    ])

    print(f"Built Law database with {Law.objects.count()} laws")


def process_laws():
    '''    
    Convert Law model to EmbeddedLaw model.
    This function processes all Law objects, creates corresponding EmbeddedLaw objects,
    and performs necessary transformations and embeddings. It's designed to prepare
    the law data for more efficient searching and processing.
    '''
    batch_size = 1000
    try:
        # Clear existing EmbeddedLaw objects if needed
        # EmbeddedLaw.objects.all().delete()  # Uncomment if you want to clear existing data

        # Initialize a list to hold EmbeddedLaw instances
        embedded_laws_batch = []

        # Iterate through Law objects in batches
        for law in Law.objects.iterator(chunk_size=batch_size):
            # Create a new EmbeddedLaw object with transformed data
            embedded_law = EmbeddedLaw(
                law_id=law.id,
                book_code=law.book_code,
                title=law.title,
                text=law.text,
                source_url=law.source_url,
                text_reduced=law.text[:EmbeddedLaw.reduced_text_length],
                embedding_text=law.text  # Placeholder for text enrichment
                # embedding_base and embedding_optimized can be set after generating embeddings
            )

            # Append to the batch list
            embedded_laws_batch.append(embedded_law)


            # When the batch size is reached, bulk create the EmbeddedLaw objects
            if len(embedded_laws_batch) >= batch_size:
                with transaction.atomic():
                    EmbeddedLaw.objects.bulk_create(embedded_laws_batch, ignore_conflicts=True)
                print(f"Processed and saved batch of {len(embedded_laws_batch)} EmbeddedLaw objects.")
                # Clear the batch list for the next set of objects
                embedded_laws_batch.clear()


    except Exception as e:
        print(f"Error processing laws: {e}")


def populate_law_db():
    if not settings.USE_TEST_DB:
        print("Test database population skipped: USE_TEST_DB is False")
        return

    # Use the correct path for the test database
    test_db_path = os.path.join(settings.BASE_DIR, 'old_law_db.sqlite3')
    
    if not os.path.exists(test_db_path):
        print(f"Test database not found at {test_db_path}")
        return

    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT external_id, book_code, title, text FROM OpenLegalDataLaw")
    laws = cursor.fetchall()

    # Clear existing data
    OpenLegalDataLawTest.objects.all().delete()

    # Bulk create new objects
    OpenLegalDataLawTest.objects.bulk_create([
        OpenLegalDataLawTest(
            external_id=law[0],
            book_code=law[1],
            title=law[2],
            text=law[3],
            text_char=law[3][:1024]
        ) for law in laws
    ])

    conn.close()
    print(f"Populated {len(laws)} laws into OpenLegalDataLawTest")


