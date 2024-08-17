
# from django.http import JsonResponse


# def search(request):
#     query = request.GET.get('q', '')
#     results = {
#         'query': query,
#         'results': [f"Result 1 for {query}", f"Result 2 for {query}"]
#     }
#     return JsonResponse(results)


from django.http import HttpResponse
from django.http import JsonResponse

def search(request):
    query = request.GET.get('q', None)
    # If the query is empty, return an error

    results = {
        'query': query,
        'results': []      
    }

    if not query or query.strip() == "":
        results["error"] = "Please enter a search query"
        return JsonResponse(results)
    elif len(query) < 3:
        results["error"] = "Please enter at least 3 characters"
        return JsonResponse(results)
    
    result_list = [{"id": 1, "title": "Title 1", "text": "Text 1"},
                    {"id": 2, "title": "Title 2", "text": "Text 2"},
                    {"id": 3, "title": "Title 3", "text": "Text 3"}]

    results["query"] = query
    results["results"] = result_list
    
    return JsonResponse(results)