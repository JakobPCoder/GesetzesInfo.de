from django.urls import path
from . import views

urlpatterns = [
    path('api/search/', views.search, name='search'),
    path('api/laws/count/', views.law_count, name='law_count'),
    path('api/keywords/count/', views.keyword_count, name='keyword_count'),
]
