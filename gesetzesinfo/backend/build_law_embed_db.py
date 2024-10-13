import sqlite3
import sys
import os
import re
from datetime import datetime
from typing import List
from openai import OpenAI
import tiktoken
from tqdm import tqdm  # Add this import at the top
import pickle  # Add this import at the top
import numpy as np
import faiss

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_app.util import clear_text
from dotenv import dotenv_values

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_path = os.path.join(parent_dir, '.env')

# Load the environment variables
env_vars = dotenv_values(env_path)


REBUILD = True


# Check if OPENAI_API_KEY is in the loaded variables
if 'OPENAI_API_KEY' in env_vars:
    api_key = env_vars['OPENAI_API_KEY']
    print(f"OPENAI_API_KEY: {api_key[:5]}...{api_key[-5:]}")
    print("dimesions", env_vars.get('EMBEDDING_MODEL_DIMS'))
else:
    print("OPENAI_API_KEY not found in .env file")

# Connect to the law_db database in the backend folder
db_path = os.path.join(current_dir, 'law_db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

OVERLAP_RATIO = 0.5 


def clamp_text_to_tokens(text: str, max_tokens: int):
    if len(text) > max_tokens:
        encoding = tiktoken.encoding_for_model(env_vars.get('EMBEDDING_MODEL'))
        encoded_text = encoding.encode(text)
        num_tokens = len(encoded_text)
        if num_tokens > max_tokens:
            text = encoding.decode(encoded_text[:max_tokens])
        return text
    else:
        return text
    
def law_to_text(law: dict) -> str:

    text = f"Gesetz: {law['title']}\n\nGesetzbuch: {law['book_code']}\n\nText: {law['text']}"
    
    if not text:
        text = "Text nicht vorhanden :("

    return text


def embed_laws(laws: List[dict]) -> List[dict]:
    """
    Embed the text of multiple laws using the OpenAI API.

    Args:
        laws (List[dict]): A list of dictionaries, each containing law information
                           (id, title, text, book_code).

    Returns:
        List[dict]: A list of dictionaries, each containing the original law information
                    and an additional 'embedding' key with the embedding vector.

    Raises:
        ValueError: If the OpenAI API key is not set.
        Exception: For any errors during the embedding process.
    """
    api_key = env_vars.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key is not set in the environment variables.")

    # Combine and limit all texts to env EMBEDDING_MODEL_MAX_TOKENS
    max_tokens = int(env_vars.get('EMBEDDING_MODEL_MAX_TOKENS', 8191))
    combined_texts = [clamp_text_to_tokens(law_to_text(law), max_tokens) for law in laws]

    response = OpenAI(api_key=api_key).embeddings.create(
        model=env_vars.get('EMBEDDING_MODEL'),
        input=combined_texts,
        encoding_format='float',
        dimensions=int(env_vars.get('EMBEDDING_MODEL_DIMS'))
    )

    actual_dims = len(response.data[0].embedding)
    expected_dims = int(env_vars.get('EMBEDDING_MODEL_DIMS'))
    if actual_dims != expected_dims:
        print(f"Warning: Actual embedding dimensions ({actual_dims}) do not match expected dimensions ({expected_dims})")

    embeddings = [item.embedding for item in response.data]
    
    laws_copy = laws.copy()
    for law, embedding in zip(laws_copy, embeddings):
        law['embedding'] = embedding
    
    return laws_copy



def create_embedded_laws_table():
    # Drop the existing table if it exists
    
    if REBUILD:
        cursor.execute('DROP TABLE IF EXISTS embedded_laws')
    
    # Create the new table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS embedded_laws (
        id INTEGER PRIMARY KEY,
        law_id INTEGER,
        book_code TEXT,
        title TEXT,
        text TEXT,
        source_url TEXT,
        embedding BLOB,
        FOREIGN KEY (law_id) REFERENCES laws(id)
    )
    ''')
    conn.commit()


def fetch_new_laws(batch_size):
    last_id = 0
    while True:
        cursor.execute('''
            SELECT l.id, l.title, l.text, l.book_code, l.source_url
            FROM laws l
            LEFT JOIN embedded_laws el ON l.id = el.law_id
            WHERE el.id IS NULL AND l.id > ?
            ORDER BY l.id
            LIMIT ?
        ''', (last_id, batch_size))
        batch = cursor.fetchall()
        
        if not batch:
            print("No more laws to fetch")
            break
        
        yield batch
        last_id = batch[-1][0]



def process_new_laws():
    """
    Process new laws by embedding their text and storing the embeddings in the database.

    This function:
    1. Creates the embedded_laws table if it doesn't exist.
    2. Fetches new laws that haven't been embedded yet.
    3. Embeds the text of these laws using the OpenAI API.
    4. Stores the embeddings in the embedded_laws table.
    5. Provides progress updates and final statistics.

    The function processes laws in batches to manage memory usage and API calls efficiently.
    """
    create_embedded_laws_table()
    batch_size = 512

    # Count new laws to process
    cursor.execute('''
        SELECT COUNT(*) 
        FROM laws l
        LEFT JOIN embedded_laws el ON l.id = el.law_id
        WHERE el.id IS NULL
    ''')
    total_new_laws = cursor.fetchone()[0]
    print(f"Total new laws to process: {total_new_laws}")

    if total_new_laws == 0:
        print("No new laws to process.")
        return

    with tqdm(total=total_new_laws, desc="Processing new laws") as pbar:
        for batch in fetch_new_laws(batch_size):
            laws = [
                {
                    'id': law[0],
                    'title': law[1],
                    'text': law[2],
                    'book_code': law[3],
                    'source_url': law[4]
                }
                for law in batch
            ]
     
            embedded_laws = embed_laws(laws)

            # Prepare and insert data
            valid_data = [
                ( law['book_code'], law['title'], law['text'], law['source_url'], np.array(law['embedding']).astype(np.float32).tobytes())
                for law in embedded_laws
            ]

            cursor.executemany('''
            INSERT INTO embedded_laws (book_code, title, text, source_url, embedding)
            VALUES (?, ?, ?, ?, ?)
            ''', valid_data)

            conn.commit()
            pbar.update(len(embedded_laws))

    # Final statistics
    cursor.execute("SELECT COUNT(*) FROM embedded_laws")
    total_embedded_laws = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT law_id) FROM embedded_laws")
    unique_embedded_laws = cursor.fetchone()[0]
    print(f"Total embedded laws in the database: {total_embedded_laws}")
    print(f"Unique laws with embeddings: {unique_embedded_laws}")

    # get and print the legnth of an embedding


def build_vector_db():
    """
    Build a FAISS vector database from embedded laws stored in SQLite.

    This function:
    1. Fetches all embedded laws from the database.
    2. Creates a FAISS index using the embeddings.
    3. Saves the index to a file named 'law_vector_db.faiss'.

    The function provides progress updates and handles potential errors.
    """
    cursor.execute('SELECT id, embedding FROM embedded_laws')
    results = cursor.fetchall()

    print(f"Found {len(results)} embedded laws in the database.")

    if not results:
        print("No embedded laws found in the database.")
        return

    ids = np.array([row[0] for row in results], dtype=np.int64)
    embeddings = np.array([np.frombuffer(row[1], dtype=np.float32) for row in results])

    print(f"Number of embeddings: {len(embeddings)}")
    print(f"Number of ids: {len(ids)}")

    if len(embeddings) == 0 or len(ids) == 0:
        print("No data to add to the index.")
        return

    # print length of a signle embedding
    print(f"Length of a single embedding: {len(embeddings[0])}")


    dimension = len(embeddings[0])
    print(f"Dimension: {dimension}")

    index = faiss.IndexFlatL2(int(env_vars.get("EMBEDDING_MODEL_DIMS")))
    id_map = faiss.IndexIDMap(index)

    print(f"Index created with dimension: {dimension}")

    id_map.add_with_ids(embeddings, ids)

    print(f"Index total after adding: {id_map.ntotal}")


    faiss.write_index(id_map, os.path.join(current_dir, 'law_vector_db.faiss')) 

    print(f"Vector database built and saved with {len(ids)} laws.")


if __name__ == '__main__':
    api_key = env_vars.get('OPENAI_API_KEY')
    print(f"OPENAI_API_KEY: ", api_key)
    print(f"EMBEDDING_MODEL: {env_vars.get('EMBEDDING_MODEL')}")
    print(f"EMBEDDING_MODEL_MAX_TOKENS: {env_vars.get('EMBEDDING_MODEL_MAX_TOKENS')}")

    process_new_laws()
    build_vector_db()  # Add this line to build the vector database

    print("Done")

# Close the database connection
conn.close()

