import json
import re
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpRequest
from django.db.models import Q, Count, F, Value, IntegerField, FloatField, Sum, ExpressionWrapper, Case, When
from django.db.models.functions import Greatest, Length, Cast


from typing import List


from . import openlegaldata
from .models import get_law_model
from .embed import start_migration_task
from .util import clear_text


from django.db.models import Q
import openai
import os



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

    base_url = os.getenv("LLM_KEYWORD_EXTRACTION_HOST")
    api_key = os.getenv("GROQ_API_KEY")

    print("base_url", base_url)
    print("api_key", api_key)

    llm_client = openai.OpenAI(
        base_url=os.getenv("LLM_KEYWORD_EXTRACTION_HOST"),
        api_key=os.getenv("GROQ_API_KEY")
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
                model=os.getenv("LLM_KEYWORD_EXTRACTION_MODEL"),
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


    
    




def multi_keyword_search(keywords: list, max_results: int = 64):
    # Get the Law model dynamically
    Law = get_law_model()
    
    # Ensure we have some keywords to search for
    if not keywords:
        return Law.objects.none()

    # Create a Q object to combine all keyword conditions
    q_objects = Q()
    for keyword in keywords:
        q_objects |= Q(title__icontains=keyword) | Q(text_char__icontains=keyword)

    # Filter by the keywords
    query = Law.objects.filter(q_objects)

    results = []
    
    # Iterate through each law item in the query result
    for law in query:
        title = law.title
        text = law.text_char
        
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

        
        # Add the law's data along with counts to the results
        results.append({
            'id': law.id,
            'title': title,
            'text': text,
            'score': score
        })

    # Sort the results by score
    results = sorted(results, key=lambda x: x['score'], reverse=True)

    # limit the results to max_results
    results = results[:max_results]

    return results


  




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



    keywords = query_to_keywords_llm(query)
    print("keywords", keywords)
    
    # Call the multi_keyword_search function
    search_results = multi_keyword_search(keywords)

    # Limit the results to 64
    search_results = search_results[:64]

    # Wrap the results in a dictionary, regardless of their type
    response["results"] = search_results


    # Return the response as a dict to avoid setting `safe=False`
    return JsonResponse(response)
