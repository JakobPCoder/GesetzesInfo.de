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
from .util import clear_query


from django.db.models import Q

def query_to_keywords(query: str):
    """
    This function converts a query to a list of keywords.
    """
    query = clear_query(query)
    # remove all non-alphanumeric characters
    query = re.sub(r'[^\w\s]', '', query)
    return query.split()


def multi_keyword_search(keywords: list):
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


        score = ((title_score_unique * 5) + (text_score_unique * 3) + (text_score_total * 1)) / len(keywords)

        
        # Add the law's data along with counts to the results
        results.append({
            'id': law.id,
            'title': title,
            'text': text,
            'title_keyword_count': title_keyword_count,
            'text_keyword_count': text_keyword_count,
            'keyword_occurrences': keyword_occurrences,
            'score': score
        })

        # Sort the results by score
        results = sorted(results, key=lambda x: x['score'], reverse=True)

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
    query = clear_query(query)

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





    keywords = query_to_keywords(query)
    print("keywords", keywords)
    
    # Call the multi_keyword_search function
    search_results = multi_keyword_search(keywords)

    # Limit the results to 64
    search_results = search_results[:64]

    # Wrap the results in a dictionary, regardless of their type
    response["results"] = search_results


    # Return the response as a dict to avoid setting `safe=False`
    return JsonResponse(response)
