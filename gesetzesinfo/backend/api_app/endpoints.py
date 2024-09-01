    


from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpRequest

from . import openlegaldata
from .models import Law, OldTitleKeyword

def law_count(request):
    try:
        num_laws = Law.objects.count()
        return JsonResponse({'count': num_laws, 'error': None})
    except Exception as e:
        return JsonResponse({'count': None, 'error': str(e)})

def keyword_count(request):
    try:
        num_laws = OldTitleKeyword.objects.count()
        return JsonResponse({'count': num_laws, 'error': None})
    except Exception as e:
        return JsonResponse({'count': None, 'error': str(e)})
    

def search(request):
    """
    This function is used to search for a query in the database.

    Parameters:
    request (HttpRequest): The HTTP request object containing the query parameter.

    Returns:
    JsonResponse: A JSON response containing the search results or an error message.
    """
    query = request.GET.get('q', None)

    results = {
        'query': query,
        'results': []      
    }

    # Check if a query is provided
    if not query:
        # If no query is provided, return an error message
        results["error"] = "Please enter a search query"
        return JsonResponse(results)
    # Check if the query length is less than 3
    elif len(query) < 3:
        # If the query length is less than 3, return an error message
        results["error"] = "Please enter at least 3 characters"
        return JsonResponse(results)
    

    # Generate keywords from the query using the OpenAI API
    keywords = openlegaldata.generate_search_keywords(query)

    if keywords:
        # Iterate over the generated keywords and search for them on OpenLegalData
        for kw in keywords:
            # Search for the keyword on OpenLegalData
            kw_results = openlegaldata.law_search(kw, max_results=1024) or []

            # Add the keyword to our database, so it doesn't have to be searched for again.
            # This is done by creating an OldTitleKeyword object with the keyword and the number of results.
            kwdb = OldTitleKeyword(keyword=kw, results=len(kw_results))
            kwdb.save()

            # Consume the old laws by creating a new Law object for each result
            openlegaldata.consume_old_laws(kw_results)




    # Search for the query in the database
    # This is done by filtering the Law objects with the query as a substring of the title
    # The results are then converted to a list of dictionaries with the relevant fields
    laws = Law.objects.filter(title__icontains=query)
    laws = list(laws.values('id','external_id', 'book_code', 'title', 'text', 'source_url'))
    results["results"] = laws

    # Return the results as a JSON response
    return JsonResponse(results)
