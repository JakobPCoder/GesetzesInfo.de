import logging
import os
import random
import threading
from typing import List

from django.db import IntegrityError
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from dotenv import load_dotenv
from openai import OpenAI, LengthFinishReasonError
from pydantic import BaseModel
import numpy as np
import tiktoken
import math


from tqdm import tqdm
from api_app.models import EmbeddedLaw
load_dotenv()

enc = tiktoken.get_encoding("cl100k_base")


def split_text(text: str, max_tokens: int = 512, min_overlap: float = 0.5):
    '''
    Split the text into chunks of max_tokens that overlap by at least min_overlap * max_tokens,
    adjusting the overlap to fit the text perfectly.
    '''

    # Tokenize the input text
    tokens = enc.encode(text)
    total_tokens = len(tokens)

    # If the text is short enough, return it as a single chunk
    if total_tokens <= max_tokens:
        return [text]

    # Calculate the ideal number of chunks
    ideal_chunk_count = math.ceil(total_tokens / (max_tokens * (1 - min_overlap)))

    # Calculate the adjusted overlap
    adjusted_overlap = 1 - (total_tokens / (max_tokens * ideal_chunk_count))
    adjusted_step = int(max_tokens * (1 - adjusted_overlap))

    chunks = []
    start = 0

    # Create chunks using the adjusted overlap
    for i in range(ideal_chunk_count):
        end = min(start + max_tokens, total_tokens)
        chunk_tokens = tokens[start:end]
        chunks.append(enc.decode(chunk_tokens))
        start += adjusted_step

    return chunks


def split_texts(texts: List[str], max_tokens: int = 512, min_overlap: float = 0.5) -> List[str]:
    """
    Split multiple texts into chunks based on token limits and overlap.

    Args:
    texts (List[str]): List of input texts to be split.
    max_tokens (int): Maximum number of tokens per chunk. Default is 512.
    min_overlap (float): Minimum overlap ratio between chunks. Default is 0.5.

    Returns:
    List[str]: A flattened list of all text chunks from all input texts.
    """
    # Iterate through each text, split it into chunks, and flatten the result
    return [chunk 
            for text in tqdm(texts, desc="Splitting texts", unit="text") 
            for chunk in split_text(text, max_tokens, min_overlap)]









