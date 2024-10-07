from django.urls import path
from . import views

urlpatterns = [
    path('api/search/', views.search, name='search'),
    path('api/laws/count/', views.law_count, name='law_count'),
    path('api/laws/count_raw/', views.unprocessed_law_count, name='count_raw'),
]
