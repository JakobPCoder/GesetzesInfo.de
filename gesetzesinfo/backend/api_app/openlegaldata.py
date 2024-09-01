
import os
import requests
from typing import List

from .models import Law, LawWordDefinition, OldTitleKeyword
from django.db import IntegrityError
from openai import OpenAI, LengthFinishReasonError
from pydantic import BaseModel


import logging


def generate_search_keywords(query: str, min_kws: int = 4, max_kws: int = 16) -> List[str]:
    openai_key = os.getenv("OPENAI_API_KEY")

    if not openai_key:
        logging.info("No OpenAI API key found. Search keyword generation abandoned.")
        return []
    
    try:
        openai_client = OpenAI(api_key=openai_key)
    except Exception as e:
        logging.error(f"Failed to create OpenAI client: {e}")
        return []

    # Prompt for generating keywords
    prompt_system = f"""
Erstelle Keywords um Suchanfrangen an eine Gesetzes Datenbank zu stellen.
Als Grundlage für die Keywords dient eine query in natürlicher Sprache.
Generiere {min_kws} bis {max_kws} Keywords die die ursprüngliche Query gut umschreiben.
Die wichtigsten Inhalte und einzelne keywords aus der Query sollten erhalten bleiben.
Achte darauf, die urpsüngliche Bedeutung der Query zu includieren und darauf,
dass die Keywords im kontext von deutschen Gesetzen gesucht werden.
    """

    prompt = f"""
    Query:
    {query}
    """

    class Keywords(BaseModel):
        keywords: list[str]
        def __str__(self):
            return str(self.keywords)
        
    max_tries = 1
    success = False  
    keywords_list = []

    while not success and max_tries > 0:
        max_tries -= 1

        try:
            responses = openai_client.beta.chat.completions.parse(
                model = "gpt-4o-mini",
                messages = [{"role": "system", "content": prompt_system}, {"role": "user", "content": prompt}],
                temperature = 0.8,
                max_tokens = 2048,
                response_format = Keywords,
            )

            message = responses.choices[0].message
            if message.parsed:
                logging.info("response included parsed keywords.")
            elif message.refusal:
                logging.error("Failed to generate keyword, refusal: ", message.refusal)
                return []

            keywords_obj: Keywords = message.parsed
            logging.info("Generated keywords: ", keywords_obj)
            if len(keywords_obj.keywords) < min_kws:
                logging.error("Failed to generate enough keywords")
            else:
                success = True
                keywords_list = keywords_obj.keywords
                logging.info("Generated enough keywords: ", keywords_obj.keywords)

        except Exception as e:
            logging.error("Failed to generate keywords: ", e)
                
    if not keywords_list:
        logging.error("Failed to generate keywords")
        return []


    try:
        # Filter out the keywords that already exist in the database
        existing_keywords_qs = OldTitleKeyword.objects.filter(keyword__in=keywords_list)

        # Extract existing keywords from the queryset to a set
        existing_keywords_set = set(existing_keywords_qs.values_list('keyword', flat=True))

        # Remove existing keywords from the original list
        filtered_keywords = [keyword for keyword in keywords_list if keyword not in existing_keywords_set]
        logging.info("Filtered keywords: ", filtered_keywords)
        return filtered_keywords
    
    except Exception as e:
        logging.error("Failed to filter keywords: ", e)
        return []




def law_search(query_title: str = None, query_text: str = None, book_code: str = None, year: str = None, max_results: int = 16):
    results = []
    params = {
        "title": query_title,
        "text": query_text,
        "book_code": book_code,
        "year": year,
        "page": 1  # Start with the first page
    }

    
    headers = {
        "accept": "application/json",
        "Authorization": f"Token {os.getenv('OPENLEGALDATA_TOKEN')}",
    }
    
    while len(results) < max_results:
        response = requests.get("https://de.openlegaldata.io/api/laws/search/", params=params, headers=headers)
        data = response.json()
        results.extend(data['results'])

        # Check if there is a next page
        if not data['next']:
            break  # No more pages, exit the loop

        # Increment the page number for the next request
        params["page"] += 1

    # Return only up to max_results
    return results[:max_results]




def consume_old_laws(laws_data: list):
    laws_to_create = []
    for law_data in laws_data:
        law = validate_new_old_law(law_data)
        if law:
            laws_to_create.append(law)

    if not laws_to_create:
        logging.info("No new laws were created")
        return
    
    try:
        Law.objects.bulk_create(laws_to_create)
        logging.info(f"Created {len(laws_to_create)} laws in the database")
    except IntegrityError:
        logging.error("Failed to create laws in the database")


def validate_new_old_law(law_data: dict):
    external_id = law_data.get('id', None)

    if not external_id:
        logging.error("No external id found in law data")
        return None
    
    # Check if the law already exists
    if Law.objects.filter(external_id=external_id).exists():
        logging.info(f"Law {external_id} already exists in the database")
        return None

    law = create_law_from_old_json(law_data)

    if law:
        return law
    else:
        logging.error("Failed to create law from old json")
        return None

def create_law_from_old_json(law_data: dict):
     # Extract the main law information
    external_id = law_data.get('id', None)
    book_code = law_data.get('book_code', None)
    title = law_data.get('title', None)
    text = law_data.get('text', None)

    source_url = "https://de.openlegaldata.io/"

    if not external_id or not book_code or not title or not text:
        logging.error("No external id, book code, title or text found in law data")
        return None

    law = Law(external_id=external_id, book_code=book_code, title=title, text=text, source_url=source_url)

    return law


