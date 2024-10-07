import sqlite3
import sys
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from api_app.util import clear_text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_app.openlegaldata import law_search
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Connect to the test database in the backend folder
db_path = os.path.join(current_dir, 'law_db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Drop the existing table if it exists
cursor.execute('DROP TABLE IF EXISTS OpenLegalDataLaw')

# Create the OpenLegalDataLaw table
cursor.execute('''
CREATE TABLE IF NOT EXISTS OpenLegalDataLaw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id INTEGER UNIQUE,
    book_code TEXT,
    title TEXT,
    text TEXT
)
''')

# List of search queries
search_queries = [
    "Grundgesetz",
    "BGB",
    "StGB",
    "SGB",
    "HGB",
    "ZPO",
    "StPO",
    "StVO"
]

# Set a high max_results value
max_results = 10000

# Maximum number of concurrent tasks
max_concurrent_tasks = 6

async def fetch_laws(query):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        try:
            print(f"Searching for '{query}'...")
            laws = await loop.run_in_executor(pool, law_search, query, None, None, None, max_results)
            print(f"API call for '{query}' completed. Found {len(laws)} entries.")
            if len(laws) == 0:
                print(f"No results for '{query}'. Response: {laws}")
            return laws
        except Exception as e:
            print(f"Error searching for '{query}': {str(e)}")
            return []

async def main():
    all_laws = []
    sem = asyncio.Semaphore(max_concurrent_tasks)

    async def bounded_fetch(query):
        async with sem:
            return await fetch_laws(query)

    tasks = [bounded_fetch(query) for query in search_queries]
    results = await asyncio.gather(*tasks)

    for laws in results:
        all_laws.extend(laws)

    # Deduplicate laws based on external_id
    unique_laws = {law['id']: law for law in all_laws}.values()

    # Clear the text
    print("Clearing the text...")
    for law in unique_laws:
        law['text'] = clear_text(law['text'])

    # Clear the database completely
    cursor.execute("DELETE FROM OpenLegalDataLaw")

    # Insert or update laws in the database
    for law in unique_laws:
        cursor.execute('''
        INSERT OR IGNORE INTO OpenLegalDataLaw (external_id, book_code, title, text)
        VALUES (?, ?, ?, ?)
        ''', (str(law['id']), law['book_code'], law['title'], law['text']))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print(f"\nTotal laws found: {len(all_laws)}")
    print(f"Unique laws after deduplication: {len(unique_laws)}")
    print(f"Test database created with {len(unique_laws)} unique laws.")

# Run the async main function
asyncio.run(main())
