
from django.http import JsonResponse, HttpResponse, HttpRequest
from .models import EmbeddedLaw, SearchQuery, Lock
import numpy as np

from .util import clamp, lerp
import faiss
import os


LOCK_NAME = 'index_update_lock'


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
INDEX_PATH = os.path.join(parent_dir, 'law_vector_db.faiss')


def calc_new_embedding(
    query_embedding: np.ndarray, 
    law_embedding: np.ndarray, 
    score: float
) -> np.ndarray:
    '''
    Calculate the new embedding based on the query embedding and the law embedding

    Parameters:
    query_embedding (np.ndarray): The embedding of the query
    law_embedding (np.ndarray): The embedding of the law
    score (float): The score of the rating

    Returns:
    np.ndarray: The new embedding
    '''

    factor = clamp(score, -1.0, 1.0) / 10

    adjusted_embedding = lerp(law_embedding, query_embedding, factor)

    return adjusted_embedding


def rating_to_score(rating: str) -> float:
    '''
    Convert a rating to a score

    Parameters:
    rating (str): The rating ("positive" or "negative")

    Returns:
    float: The score
    '''

    if rating == "positive":
        return 1.0
    elif rating == "negative":
        return -1.0
    else:
        return 0.0
    
def rebuild_index():

    # Acquire the lock
    lock = Lock.acquire_lock(LOCK_NAME)
    if not lock:
        print("Failed to acquire lock")
        return 

    try:
        # Get all current IDs and optimized embeddings from the database
        laws = EmbeddedLaw.objects.all()
        ids = np.array([law.id for law in laws])
        embeddings = np.array([law.get_embedding_optimized() for law in laws])
        
        # Create a new index
        index = faiss.IndexFlatL2(embeddings.shape[1])
        
        # Add the IDs and embeddings to the index
        id_map = faiss.IndexIDMap(index)
        id_map.add_with_ids(embeddings, ids)
        
        # Save the updated index back to the file
        faiss.write_index(id_map, INDEX_PATH)
        
        print("Rebuilt index with new embeddings")
    
    except Exception as e:
        print(f"Error rebuilding index: {e}")

    # Release the lock
    Lock.release_lock(LOCK_NAME)


def rating_endpoint(request) -> JsonResponse:
    """
    Update the embedding of the law that was rated based on the query and rating.

    Parameters:
    request (HttpRequest): The HTTP request with the following query parameters:
        id (int): The id of the law to rate
        qid (int): The id of the search query
        r (str): The rating ("positive" or "negative")

    Returns:
    JsonResponse: A JSON response containing the result of the operation
    """
    print("rating endpoint")

    # Get parameters from the request
    id: int = int(request.GET.get('id', None))
    query_id: int = int(request.GET.get('qid', None))
    rating: str = request.GET.get('r', None)

    # Validate parameters
    if not id:
        return JsonResponse({'error': 'id is required'}, status=400)
    if not query_id:
        return JsonResponse({'error': 'qid is required'}, status=400)
    if not rating:
        return JsonResponse({'error': 'r is required'}, status=400)
    
    print(f"id: {id}, query_id: {query_id}, rating: {rating}")

    valid_ratings = ["positive", "negative"]
    if rating not in valid_ratings:
        return JsonResponse({'error': f'r must be one of {", ".join(valid_ratings)}'}, status=400)

    # Get the search query that corresponds to search query and law that is being rated
    try:
        query = SearchQuery.objects.get(id=query_id)
    except SearchQuery.DoesNotExist:
        return JsonResponse({'error': f'SearchQuery with id {query_id} does not exist'}, status=404)

        
    # Get the law that is being rated
    try:
        embedded_law = EmbeddedLaw.objects.get(id=id)
    except EmbeddedLaw.DoesNotExist:
        return JsonResponse({'error': f'EmbeddedLaw with id {id} does not exist'}, status=404)

    
    # Update the embedding
    try:
        law_embedding = embedded_law.get_embedding_optimized()
    
        query_embedding = query.get_embedding()

        adjusted_embedding = calc_new_embedding(query_embedding, law_embedding, rating_to_score(rating))

        EmbeddedLaw.objects.filter(id=id).update(embedding_optimized=adjusted_embedding)

        rebuild_index()

    except Exception as e:
        return JsonResponse({'error': f"Error updating the embedding: {str(e)}"}, status=500)

    return JsonResponse({"success": True}, status=200)
0.4254