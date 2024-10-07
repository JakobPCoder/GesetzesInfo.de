import sqlite3
import sys
import os
import re
from datetime import datetime
from tqdm import tqdm  # Add this import at the top

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

def extract_section_and_title(full_title):
    """
    Return the full title without extracting section number.
    """
    return full_title

def dummy_transform(old_law):
    """
    Function to transform OpenLegalDataLaw to Law model.
    """
    title = extract_section_and_title(old_law['title'])
    return {
        'book_code': old_law['book_code'], 
        'title': title,
        'text': old_law['text'],
        'source_url': f'https://openlegaldata.io/laws/{old_law["id"]}/',
    }

def filter_law(law):
    title = law['title']
    text = law['text']

    if not title or not text or len(text) < 5 or ("(weggefallen)" in title.lower()) or ("(weggefallen)" in text.lower()):
        return False

    return True

def process_laws():
    # Drop the existing Law table if it exists
    cursor.execute('DROP TABLE IF EXISTS laws')
    
    # Create the Law table
    cursor.execute('''
    CREATE TABLE laws (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_code TEXT,
        title TEXT,
        text TEXT,
        source_url TEXT
    )
    ''')

    # Fetch all OpenLegalDataLaw entries
    cursor.execute('SELECT id, book_code, title, text FROM OpenLegalDataLaw')
    old_laws = [{'id': row[0], 'book_code': row[1], 'title': row[2], 'text': row[3]} for row in cursor.fetchall()]

    # Process each law and insert into the Law table with a loading bar
    for old_law in tqdm(old_laws, desc="Processing laws", unit="law"):
        new_law = dummy_transform(old_law)

        if not filter_law(new_law):
            continue
        
        cursor.execute('''
        INSERT INTO laws (book_code, title, text, source_url)
        VALUES (?, ?, ?, ?)
        ''', (new_law['book_code'], new_law['title'], 
              new_law['text'], new_law['source_url']))

    # Commit the changes
    conn.commit()

    # print actual db length
    cursor.execute('SELECT COUNT(*) FROM laws')
    count = cursor.fetchone()[0]
    print(f"Laws processed: {count}")
    print(f"Removed laws: {len(old_laws) - count}")

if __name__ == '__main__':
    print("Recreating laws table and processing laws...")
    process_laws()

# Close the database connection
conn.close()

