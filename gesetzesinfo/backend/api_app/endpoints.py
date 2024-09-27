from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpRequest

from . import openlegaldata
from .models import  OldTitleKeyword, get_law_model
from .search import nl_search_endpoint

def unprocessed_law_count(request):
    try:
        Law = get_law_model()
        num_laws = Law.objects.count()
        return JsonResponse({'count': num_laws, 'error': None})
    except Exception as e:
        return JsonResponse({'count': None, 'error': str(e)})

def law_count(request):
    try:
        Law = get_law_model()
        num_laws = Law.objects.count()
        return JsonResponse({'count': num_laws, 'error': None})
    except Exception as e:
        return JsonResponse({'count': None, 'error': str(e)})

def old_keywords_count(request):
    try:
        num_laws = OldTitleKeyword.objects.count()
        return JsonResponse({'count': num_laws, 'error': None})
    except Exception as e:
        return JsonResponse({'count': None, 'error': str(e)})

def search(request):
    return nl_search_endpoint(request)
