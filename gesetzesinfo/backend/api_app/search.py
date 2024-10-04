from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpRequest
from django.db.models import Q, Count, F, Value, IntegerField, FloatField, Sum, ExpressionWrapper, Case, When
from django.db.models.functions import Greatest, Length, Cast


import os
from typing import List
import json
import re
from dotenv import dotenv_values, load_dotenv
import openai
import faiss
import numpy as np

from .models import SearchRequest, get_law_model
from .util import clear_text, clamp_text_to_tokens

from django.db.models import Q, QuerySet
from .models import EmbeddedLaw
from typing import List, Dict, Any

# Get the directory of the current script

# Load the environment variables
env_vars = dotenv_values()
print(env_vars.get('OPENAI_API_KEY'))

def query_to_keywords(query: str):
    """
    This function converts a query to a list of keywords.

    Parameters:
    query (str): The query to convert to keywords.

    Returns:
    list: A list of keywords.
    """
    query = clear_text(query)
    # remove all non-alphanumeric characters
    query = re.sub(r'[^\w\s]', '', query)
    return query.split()


def query_to_keywords_llm(query: str, max_keywords: int = 32):
    """
    This function converts a query to a list of keywords using an llm.
    Parameters:
    query (str): The query to convert to keywords.

    Returns:
    list: A list of keywords.
    """

    # base_url = env_vars.get("LLM_KEYWORD_EXTRACTION_HOST")
    # api_key = env_vars.get("GROQ_API_KEY")

    # print("base_url", base_url)
    # print("api_key", api_key)

    llm_client = openai.OpenAI(
        base_url=env_vars.get("LLM_KEYWORD_EXTRACTION_HOST"),
        api_key=env_vars.get("GROQ_API_KEY")
    )

    query = clear_text(query)

    system_prompt = """
    Sie sind ein erfahrener Jurist. 
    Extrahieren bzw. generieren sie bis zu {max_keywords} relevante Keywords einer Suchanfrage.
    Achten sie dabei darauf, dass alle Keywords für keyword search über deutsche Gesetze gedacht sind.

    Erstellen sie keine Keywords die auf alle möglichen Anfragen zutreffen würden, da sie zu allgemein sind!
    Wörter wie "Recht", "Gesetz", "Urteil", "Strafgesetze", "Strafrecht", "Gericht", "Verbrechen", "Urteil" etc. 
    sind also normaler weise icht zu verwenden!

    Es ist hingegen sinnvoll, wenn sie Variationen von einem Keyword auflisten, wie z.B. 
    "Diebstahl"-> "Dieb", "Raub". 
    "Zeitraum"-> "zeitlich", "Zeit", "Datum", "Zeitpunkt".
    "Mörder"-> "Mord", "Totschlag".
    "verletzung" -> "verletzt", "angriff", "beschädigung".
    "flucht" -> "fliehen", "entfernen".

    Fokusieren sie sich bitte auf Wörter, die tatsächlich im Text der Suchanfrage erwähnt werden.
   
    Geben sie die Keywords als JSON Object zurück, das ein Feld "keywords" hat, welches ein Array von Strings ist.
    """

    user_message = f"""
    Hier ist die Suchanfrage:
    "{query}"
    """


    max_retries = 3
    retry_count = 0

    keywords = []
    while retry_count < max_retries:
        try:
            response = llm_client.chat.completions.create(
                model=env_vars.get("LLM_KEYWORD_EXTRACTION_MODEL"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1024,
                temperature=0.4,    
                response_format={ "type": "json_object" }
            )

            loaded_keywords = json.loads(response.choices[0].message.content)
            keywords = loaded_keywords.get("keywords", [])
            break

        except Exception as e:
            print(f"query_to_keywords_llm: Attempt {retry_count + 1} failed: {e}")
            retry_count += 1
            
    if not keywords:
        print(f"query_to_keywords_llm: All {max_retries} attempts failed. Defaulting to non AI keyword extraction from query.")
        keywords = query_to_keywords(query)

    return keywords


def query_to_nl_queries(query: str, max_queries: int = 4):
    """
    Refines a user's search query into multiple natural language queries using an LLM.

    Generates up to 'max_queries' refined, neutral-form queries optimized for
    searching a legal vector embedding database.

    Parameters:
    query (str): The original user query to refine.
    max_queries (int): Maximum number of refined queries to generate. Default is 4.

    Returns:
    list: Refined natural language queries as strings. Returns [original query] if processing fails.
    """

    llm_client = openai.OpenAI(
        base_url=env_vars.get("LLM_QUERIES_EXTRACTION_HOST"),
        api_key=env_vars.get("GROQ_API_KEY")
    )

    query = clear_text(query)

    system_prompt = f"""
    Sie sind ein erfahrener Jurist. 
    Sie werden eine Suchanfrage einen naiven Klienten vorgelegt bekommen und ihre Aufgabe ist es,
    diese Suchanfrage in ein oder mehrere Queries umzuwandeln, die genutzt werden können,
    um eine Vector Embedding Datenbank von deutschen Gesetzen zu durchsuchen.

    Das format bzw. die Perspektive der Suchanfrage muss in eine einheitlich neutrale Form gebracht werden,
    die  der Sprache entspricht welche in der Juristischen Literatur verwendet wird.

    Ca 4 bis 20 Worte sind eine sinnvoll Orientierung für die Länge einer solchen Query.

    Wenn die Suchanfrage komplex ist, vergleiche zwischen verschiedenen Themen erfordert, 
    oder auf andere Weise von meherern unterschiedlichen queries zu dieser Suchanfrage profitieren können,
    dann können 1 bis {max_queries} Queries erstellt werden, um mehr verschidene Themen zu berücksichtigen.

    Geben sie die Queries als JSON Object zurück, das ein Feld "queries" hat, welches ein Array von Strings ist.
    """

    user_message = f"""
    Hier ist die Suchanfrage:
    "{query}"
    """


    max_retries = 3
    retry_count = 0

    quries = []
    while retry_count < max_retries:
        try:
            response = llm_client.chat.completions.create(
                model=env_vars.get("LLM_QUERIES_EXTRACTION_MODEL"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1024,
                temperature=0.4,    
                response_format={ "type": "json_object" }
            )

            loaded_quries = json.loads(response.choices[0].message.content)
            quries = loaded_quries.get("queries", [])
            break

        except Exception as e:
            print(f"query_to_nl_queries: Attempt {retry_count + 1} failed: {e}")
            retry_count += 1
            
    if not quries:
        print(f"query_to_nl_queries: All {max_retries} attempts failed. Defaulting to the users original query.")
        quries = [query]

    return quries


    

def multi_keyword_search(keywords: list, max_results: int = 64):
    """
    This function searches for laws based on multiple keywords.

    Parameters:
    keywords (list): A list of keywords to search for.
    max_results (int): The maximum number of results to return.

    Returns:
    List[Dict[str, Any]]: A list of dictionaries containing law_id and score.
    """
    # Ensure we have some keywords to search for
    if not keywords:
        return []

    # Create a Q object to combine all keyword conditions
    q_objects = Q()
    for keyword in keywords:
        q_objects |= Q(title__icontains=keyword) | Q(text_reduced__icontains=keyword)

    # Filter by the keywords
    query = EmbeddedLaw.objects.filter(q_objects)

    results = []
    
    # Iterate through each law item in the query result
    for law in query:
        title = law.title
        text = law.text_reduced
        
        # Initialize counters for the current law entry
        title_keyword_count = 0
        text_keyword_count = 0
        keyword_occurrences = 0

        # Check for unique keywords
        for keyword in keywords:
            # Check if keyword is in title
            if keyword.lower() in title.lower():
                title_keyword_count += 1

            # Check if keyword is in text
            if keyword.lower() in text.lower():
                text_keyword_count += 1

            # Count occurrences in text for each keyword
            text_count = text.lower().count(keyword.lower())
            keyword_occurrences += text_count

        title_score_unique =  (title_keyword_count) / len(title) if title_keyword_count > 0 else 0.0
        text_score_unique  = (text_keyword_count) / len(text) if text_keyword_count > 0 else 0.0
        text_score_total = (text_keyword_count) / len(text) if text_keyword_count > 0 else 0.0


        score = ((title_score_unique * 10) + (text_score_unique * 3) + (text_score_total * 1)) / len(keywords)

        
        # Add the law's id and score to the results
        results.append({
            'law_id': law.law_id,
            'score': score
        })

    # Sort the results by score
    results = sorted(results, key=lambda x: x['score'], reverse=True)

    return results


def get_embedding(text: str):
    """
    This function uses the openai embedding model to get the embedding for a given text.

    Parameters:
    text (str): The text to get the embedding for.

    Returns:
    list: A list of the embedding.
    """
    api_key = env_vars.get("OPENAI_API_KEY")

    # print("api_key", api_key)
    
    openai_client = openai.OpenAI(
        api_key=api_key
    )

    # Combine and limit all texts to env EMBEDDING_MODEL_MAX_TOKENS
    max_tokens = int(env_vars.get('EMBEDDING_MODEL_MAX_TOKENS', 8191))
    combined_texts = clamp_text_to_tokens(text, max_tokens)

    response = openai_client.embeddings.create(
        model=env_vars.get('EMBEDDING_MODEL'),
        input=combined_texts,
        encoding_format='float',
        dimensions = int(env_vars.get('EMBEDDING_MODEL_DIMS')) 
    )

    embedding = response.data[0].embedding

    return embedding



def natural_language_search(query: str, max_results: int = 64):
    """
    This function uses text embeddings to find the max_results nearest neighbors in the database.

    Parameters:
    query (str): The query to search for.
    max_results (int): The maximum number of results to return.

    Returns:
    List[Dict[str, Any]]: A list of dictionaries containing law_id and score.
    """

    api_key = env_vars.get("OPENAI_API_KEY")
    print("api_key", api_key)

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # load the faiss database
    faiss_db_path = os.path.join(parent_dir, 'law_vector_db.faiss')
    index = faiss.read_index(faiss_db_path)

    # get the embedding for the query
    embedding = get_embedding(query)

    # get the nearest neighbors
    distances, indices = index.search(np.array([embedding]).astype('float32'), max_results)

    print(len(indices[0]))

    # Sort indices by distances and create result list
    results = [
        {
            'law_id': int(idx),
            'score': float(1 / (1 + distance))  # Convert distance to a score between 0 and 1
        }
        for distance, idx in sorted(zip(distances[0], indices[0]), key=lambda x: x[0])
    ]

    return results


def search_results_to_output(search_results):
    # Create a dictionary to map law_id to score
    score_map = {result['law_id']: result['score'] for result in search_results}

    # Get the laws based on law_ids
    law_ids = [result['law_id'] for result in search_results]
    laws = EmbeddedLaw.objects.filter(law_id__in=law_ids)

    print(f"Number of search results: {len(search_results)}")
    print(f"Number of laws fetched: {len(laws)}")

    # Prepare the final results
    final_results = []
    for law in laws:
        final_results.append({
            'id': law.id,
            'title': law.title,
            'text': law.text,
            'score': score_map.get(law.law_id, 0)  # Use the corresponding score or 0 if not found
        })

    # Sort the final results by score in descending order
    final_results.sort(key=lambda x: x['score'], reverse=True)

    return final_results




def smart_search(query: str, max_results: int = 64, max_sub_queries: int = 4):
    """


    Parameters:
    query (str): The query to search for.
    max_results (int): The maximum number of results to return.

    Returns:
    List[Dict[str, Any]]: A sorted list of dictionaries containing id (index of the list), book_code, title, text, the id of the query it belongs toand score.
    """

    # Add the seach request to the database
    search_request = SearchRequest(search_text=query, search_text_reduced=query[:SearchRequest.reduced_text_length])
    search_request.save()

    # First get max_sub_queries queries from the query
    queries = query_to_nl_queries(query, max_sub_queries)

    print("queries", queries)

    # Then search for each query
    search_results = []
    for query in queries:


        search_results.extend(natural_language_search(query, max_results))






def nl_search_endpoint(request):
    """
    This function is used to search for a query in the database.

    Parameters:
    request (HttpRequest): The HTTP request object containing the query parameter.

    Returns:
    JsonResponse: A JSON response containing the search results or an error message.
    """
    query = request.GET.get('q', '')
    query = clear_text(query)

    response = {
        'query': query,
    }

    min_query_length = 3

    # Check if a query is provided
    if not query:
        response["error"] = "Please enter a search query"
        return JsonResponse(response, status=400)

    elif len(query) < min_query_length:
        response["error"] = f"Please enter at least {min_query_length} characters"
        return JsonResponse(response)




    # keywords = query_to_keywords_llm(query)
    # print("keywords", keywords)
    
    # # Call the multi_keyword_search function
    # search_results = multi_keyword_search(keywords)

    search_results = natural_language_search(query)


    search_results = search_results_to_output(search_results)   


    # Wrap the results in a dictionary, regardless of their type
    response["results"] = search_results


    # Return the response as a dict to avoid setting `safe=False`
    return JsonResponse(response)
