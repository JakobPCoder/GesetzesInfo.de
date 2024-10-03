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

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_app.util import clear_text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Connect to the law_db database in the backend folder
db_path = os.path.join(current_dir, 'law_db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

OVERLAP_RATIO = 0.5 

def clamp_text_to_tokens(text: str, max_tokens: int):

    # only run this id the char length is longer than the max tokens
    if len(text) > max_tokens:
        # use tiktoken to count the tokens
        encoding = tiktoken.encoding_for_model(os.getenv('EMBEDDING_MODEL'))
        encoded_text = encoding.encode(text)
        num_tokens = len(encoded_text)
        if num_tokens > max_tokens:
            text = encoding.decode(encoded_text[:max_tokens])
        return text
    else:
        return text


def embed_texts(texts: List[str]):
    print(os.getenv('OPENAI_API_KEY'))

    client_openai = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY')
    )

    # Limit all texts to env EMBEDDING_MODEL_MAX_TOKENS
    texts = [clamp_text_to_tokens(text, int(os.getenv('EMBEDDING_MODEL_MAX_TOKENS'))) for text in texts]

    batch_size = 128

    embeddings = []

    # Process texts in batches
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding texts"):
        # get the batch
        batch = texts[i:i+batch_size]

        try:
            response = client_openai.embeddings.create(
                model=os.getenv('EMBEDDING_MODEL'),  # You can change this to the model you prefer
                input=batch,
                encoding_format='float',
            )
            batch_embeddings = [item['embedding'] for item in response['data']]
            embeddings.extend(batch_embeddings)

        except Exception as e:
            embeddings.extend([None] * len(batch))
            print(f"Error in batch {i//batch_size}: {str(e)}")


    return embeddings
            # You might want to implement retry logic here



def create_embedded_laws_table():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS embedded_laws (
        id INTEGER PRIMARY KEY,
        law_id INTEGER,
        text TEXT,
        embedding BLOB,
        FOREIGN KEY (law_id) REFERENCES laws(id)
    )
    ''')
    conn.commit()


def fetch_laws(batch_size):
    offset = 0
    while True:
        cursor.execute('SELECT id, text FROM laws LIMIT ? OFFSET ?', (batch_size, offset))
        batch = cursor.fetchall()
        if not batch:
            break
        yield batch
        offset += batch_size


def process_laws():
    create_embedded_laws_table()
    batch_size = 100

    # Get total number of laws for the progress bar
    cursor.execute('SELECT COUNT(*) FROM laws')
    total_laws = cursor.fetchone()[0]

    with tqdm(total=total_laws, desc="Processing laws") as pbar:
        for batch in fetch_laws(batch_size):
            law_ids, texts = zip(*batch)
            cleaned_texts = [clear_text(text) for text in texts]
            embeddings = embed_texts(cleaned_texts)

            # Filter out None embeddings and prepare data for insertion
            valid_data = [
                (law_id, text, np.array(embedding).tobytes())
                for law_id, text, embedding in zip(law_ids, texts, embeddings)
                if embedding is not None
            ]

            cursor.executemany('''
            INSERT INTO embedded_laws (law_id, text, embedding)
            VALUES (?, ?, ?)
            ''', valid_data)

            conn.commit()
            pbar.update(len(batch))

    print("Finished processing all laws")



def get_table_length(table_name):
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    return cursor.fetchone()[0]

print(f"Number of laws in 'laws' table: {get_table_length('laws')}")
print(f"Number of embedded laws in 'embedded_laws' table: {get_table_length('embedded_laws')}")


if __name__ == '__main__':

    process_laws()
    print("Done")

# Close the database connection
conn.close()

