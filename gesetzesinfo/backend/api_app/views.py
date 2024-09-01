
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
from django.http import HttpRequest

from . import endpoints

def search(request):
    return endpoints.search(request)

def law_count(request):
    return endpoints.law_count(request) 

def keyword_count(request):
    return endpoints.keyword_count(request)