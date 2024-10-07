from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpRequest

from . import openlegaldata
from .models import  OldTitleKeyword, Law, EmbeddedLaw
from .search import search_endpoint

def unprocessed_law_count(request):
    try:
        num_laws = Law.objects.count()
        return JsonResponse({'count': num_laws, 'error': None})
    except Exception as e:
        return JsonResponse({'count': None, 'error': str(e)})

def law_count(request):
    try:
        num_laws = EmbeddedLaw.objects.count()
        print(f"num_laws: {num_laws}")
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
    return search_endpoint(request)
