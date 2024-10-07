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
import tiktoken
from together import Together
import faiss
import numpy as np

from .models import SearchRequest, SearchQuery, EmbeddedLaw
from .util import clear_text, clamp_text_to_tokens, lerp

from django.db.models import Q, QuerySet
from typing import List, Dict, Any
from functools import partial


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

    llm_client = openai.OpenAI(
        base_url=env_vars.get("LLM_KEYWORD_EXTRACTION_HOST"),
        api_key=env_vars.get("GROQ_API_KEY")
    )

    query = clear_text(query)

    system_prompt = """
    Sie sind ein erfahrener Jurist. 
    Extrahieren bzw. generieren sie 1 bis {max_keywords} relevante Keywords aus einer Suchanfrage.
    Achten sie dabei darauf, dass alle Keywords für keyword search über deutsche Gesetze gedacht sind.

    Beispiele:
    Suchanfrage: "stgb 107c"
    Keywords: ["StGB 107c", "StGB § 107c", "strafgesetzbuch", "§ 107"]

    Suchanfrage: "was ist der unterschied zwischen diesbtahl und raub?"
    Keywords: ["Diebstahl", "Raub", "entwenden", "entwendet", "Entwendung", "wegnimmt", "Wegnahme", "Besitz", "Eigentum"]

    Suchanfrage: "Artikel 19"
    Keywords: ["Artikel 19", "Grundgesetz 19", "Artikel", "Grundgesetz"]

    Suchanfrage: "fahrerflucht"
    Keywords: ["Fahrerflucht", "Flucht", "Unfall", "Fahrer", "wegfahren", "entfernen", "stvo"]

    Suchanfrage: "was ist mord"
    Keywords: ["Mord", "Mörder", "Töten", "tötet", "Totschlag", "Körperverletzung", "Todesfolge"]

    Extrahieren sie nun die 1 bis {max_keywords} relevanten Keywords.
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
                max_tokens=max_keywords * 16,
                temperature=0.7,    
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


def get_embedding(text: str):
    """
    This function uses the openai embedding model to get the embedding for a given text.

    Parameters:
    text (str): The text to get the embedding for.

    Returns:
    list: A list of the embedding.
    """
    
    openai_client = openai.OpenAI(
        api_key=env_vars.get("OPENAI_API_KEY")
    )

    # Combine and limit all texts to env EMBEDDING_MODEL_MAX_TOKENS
    clamped_text = clamp_text_to_tokens(text, int(env_vars.get('EMBEDDING_MODEL_MAX_TOKENS', 8191)))

    response = openai_client.embeddings.create(
        model=env_vars.get('EMBEDDING_MODEL'),
        input=clamped_text,
        encoding_format='float',
        dimensions = int(env_vars.get('EMBEDDING_MODEL_DIMS')) 
    )

    embedding = np.asarray(response.data[0].embedding, dtype=np.float32)

    return embedding



def calculate_keyword_score(law: EmbeddedLaw, keywords: list):
    title = law.title
    text = law.text
    title_word_count = len(title.split())
    text_word_count = len(text.split())
    
    title_keyword_count = sum(keyword.lower() in title.lower() for keyword in keywords)
    text_keyword_count = sum(keyword.lower() in text.lower() for keyword in keywords)
    keyword_occurrences = sum(text.lower().count(keyword.lower()) for keyword in keywords)

    title_score_unique = (title_keyword_count) / title_word_count if title_keyword_count > 0 else 0.0
    text_score_unique = (text_keyword_count) if text_keyword_count > 0 else 0.0
    text_score_total = (keyword_occurrences) if keyword_occurrences > 0 else 0.0

    score = ((title_score_unique * 5) + (text_score_unique * 0.3) + (text_score_total * 0.1)) / len(keywords)

    return {'law_id': law.law_id, 'score': score}


def multi_keyword_search(keywords: list, max_results: int = 64):
    """
    This function performs a multi-keyword search in the EmbeddedLaw database.

    Parameters:
    keywords (list): A list of keywords to search for in the law titles and texts.
    max_results (int): The maximum number of results to return (default is 64).

    Returns:
    list: A list of dictionaries containing the law_id and score for each matching law.
    """

    if not keywords:
        return []

    q_objects = Q()
    for keyword in keywords:
        q_objects |= Q(title__icontains=keyword) | Q(text_reduced__icontains=keyword)

    db_query = EmbeddedLaw.objects.filter(q_objects)

    # Map the score calculator over all laws in the query
    results = list(map(lambda law: calculate_keyword_score(law, keywords), db_query))

    # Sort the results by score and limit to max_results
    results = sorted(results, key=lambda x: x['score'], reverse=True)[:max_results]

    return results

def rerate_keyword_search_results(keyword_search_results: List[dict], query_embedding: np.array) -> List[dict]:
    """
    Re-rates the keyword search results by comparing their embeddings to the query embedding.

    Parameters:
    keyword_search_results (List[dict]): The keyword search results to re-rate.
    query_embedding (np.array): The embedding of the query.
    max_results (int): The maximum number of results to return (default is 64).

    Returns:
    List[dict]: The re-rated keyword search results.
    """

    # Get the embeddings for the keyword search results
    relevant_laws = EmbeddedLaw.objects.filter(law_id__in=[result['law_id'] for result in keyword_search_results])
    embeddings = [law.get_embedding_base() for law in relevant_laws]

    embedding_count = len(embeddings)
    print("embeddings", embedding_count)



    # build temproary index
    index = faiss.IndexIDMap(faiss.IndexFlatL2(int(env_vars.get('EMBEDDING_MODEL_DIMS'))))
    index.add_with_ids(np.array(embeddings, dtype=np.float32), np.array([law.law_id for law in relevant_laws]))

    # search
    distances, ids = index.search(np.array([query_embedding], dtype=np.float32), embedding_count)

    # Calculate the scores
    scores = [1 / (1 + distance) for distance in distances[0]]

    # Combine the scores with the keyword search results
    results = [{'law_id': law.law_id, 'score': score} for law, score in zip(relevant_laws, scores)]

    # Sort the results by score and limit to max_results
    results = sorted(results, key=lambda x: x['score'], reverse=True)

    return results

def natural_language_search(embedding: np.array, max_results: int = 64) -> List[dict] :
    """
    This function performs a natural language search using the provided embedding.

    Parameters:
    embedding (np.array): The embedding of the query text.
    max_results (int): The maximum number of results to return (default is 64).

    Returns:
    list: A list of dictionaries containing the law_id and score for each matching law.
    """

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    faiss_db_path = os.path.join(parent_dir, 'law_vector_db.faiss')
    vector_index = faiss.read_index(faiss_db_path)

    # Get the nearest neighbors
    distances, indices = vector_index.search(np.asarray([embedding], dtype=np.float32), max_results)
    distances, indices = distances[0], indices[0]

    # Sort indices by distances and create result list
    results = list(map(lambda idx, distance: {
        'law_id': int(idx),
        'score': float(1 / (1 + distance))
    }, indices, distances))

    return results


def search_results_to_output(search_results):
    # Create a dictionary to map law_id to score
    score_map = {result['law_id']: result['score'] for result in search_results}

    # Get the laws based on law_ids
    law_ids = [result['law_id'] for result in search_results]
    laws = EmbeddedLaw.objects.filter(law_id__in=law_ids)

    # Prepare the final results
    final_results = []
    for law in laws:
        final_results.append({
            'id': law.id,
            'title': law.title,
            'text': law.text,
            'score': score_map.get(law.law_id, 0)  # Use the corresponding score or 0 if not found
        })

    # print(final_results)

    # Sort the final results by score in descending order
    final_results.sort(key=lambda x: x['score'], reverse=True)
    return final_results



def clamp_text_to_tokens(text: str, max_tokens: int):
    """
    Clamp a given text to a certain number of tokens.

    This function is used to limit the input text to the OpenAI embedding model to a certain number of tokens.
    If the text is longer than the specified number of tokens, it is truncated to fit the model's input size.

    Parameters:
    text (str): The text to clamp.
    max_tokens (int): The maximum number of tokens to allow.

    Returns:
    str: The clamped text.
    """
    if len(text) > max_tokens:
        encoding = tiktoken.encoding_for_model(env_vars.get('EMBEDDING_MODEL'))
        encoded_text = encoding.encode(text)
        num_tokens = len(encoded_text)
        if num_tokens > max_tokens:
            text = encoding.decode(encoded_text[:max_tokens])
        return text
    else:
        return text

def get_or_create_search_query(query: str) -> SearchQuery:

    """
    Creates or retrieves a SearchQuery object from the database based on the given query.

    The query is first truncated to fit the SearchRequest model's reduced_text_length, then
    a SearchRequest object is created or retrieved from the database. If the SearchRequest
    object is created, a new SearchQuery object is created with the truncated query and
    an embedding generated from the original query. If the SearchRequest object already
    exists, the corresponding SearchQuery object is retrieved.

    Parameters:
    query (str): The query to create or retrieve a SearchQuery object for.

    Returns:
    SearchQuery: The created or retrieved SearchQuery object.
    """
    
    # Truncate the query to fit the SearchRequest model's reduced_text_length
    search_text_reduced = query[:SearchRequest.reduced_text_length]

    # Create or get a SearchRequest object
    search_request, search_request_created = SearchRequest.objects.get_or_create(
        search_text=query,
        search_text_reduced=search_text_reduced,
    )
    search_request.save()

    if not search_request_created:
        print("SearchRequest already exists")

    # Try to retrieve an existing SearchQuery object
    search_query = SearchQuery.objects.filter(query_reduced=search_text_reduced).first()

    if not search_query:
        # Create and save a new SearchQuery object
        search_query = SearchQuery.objects.create(
            search_request=search_request,
            query_text=query,
            query_reduced=search_text_reduced,
            embedding=get_embedding(query).tobytes()
        )
        search_query.save()

    return search_query


    

def filter_search_results(search_results: List[dict], max_results: int = 64, agressiveness: float = 0.5) -> List[dict]: 
    """
    Filters a list of search results based on the given agressiveness parameter.
    """

    search_results.sort(key=lambda x: x['score'], reverse=True)
    search_results = search_results[:max_results*2]

    scores = [result['score'] for result in search_results]
    mean = np.mean(scores)
    std = np.std(scores)
    threshold = mean - (std * (1.0 - agressiveness))

    filtered_results = [result for result in search_results if result['score'] > threshold]  
    filtered_results = filtered_results[:max_results]
    return filtered_results
    




def smart_search(query: str, max_results: int = 32) -> dict:
    """
    Performs a smart search on the given query, combining natural language search and keyword search.
    
    Args:
    query (str): The search query.
    max_results (int): The maximum number of results to return. Defaults to 32.
    
    Returns:
    dict: A dictionary containing the search results.
    """

    # Create a search query object with an embedding for the given query
    search_query = get_or_create_search_query(query)

    # Extract keywords from the query using a large language model
    keywords = query_to_keywords_llm(query)

    # Print the extracted keywords for debugging purposes
    print("Keywords:", keywords)

    # Calculate the maximum number of results for natural language search and keyword search
    max_nl_results = int(max_results * 2.0)
    max_keyword_results = int(max_results * 2.0)

    query_embedding = search_query.get_embedding()

    # Perform natural language search and keyword search
    nl_search_results = natural_language_search(query_embedding, max_nl_results)
    keyword_search_results = multi_keyword_search(keywords, max_keyword_results)

    # # Filter search results to ensure a balanced mix of natural language and keyword search results
    nl_search_results = filter_search_results(nl_search_results, int(max_results * 0.5), agressiveness=0.1)
    keyword_search_results = filter_search_results(keyword_search_results, int(max_results * 0.5), agressiveness=0.5)

    # Remove keyword search results that are already included in the natural language search results
    keyword_search_results = [result for result in keyword_search_results if result['law_id'] not in [r['law_id'] for r in nl_search_results]]

    # Re-rate the keyword search results based on their embeddings
    keyword_search_results = rerate_keyword_search_results(keyword_search_results, query_embedding)


    # Combine natural language search results and keyword search results
    search_results = nl_search_results + keyword_search_results 

    # Convert search results to output format
    output = search_results_to_output(search_results)

    # Return the search results in a dictionary
    return output





def search_endpoint(request):
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

    response["results"] = smart_search(query)

    # Return the response as a dict to avoid setting `safe=False`
    return JsonResponse(response)
