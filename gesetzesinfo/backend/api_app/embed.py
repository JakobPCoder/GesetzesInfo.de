

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

from openai import OpenAI, LengthFinishReasonError
from pydantic import BaseModel
import numpy as np
import tiktoken

from .models import Law, EmbeddedLaw, Lock


def law_to_text(law: Law) -> str:
    """Convert a Law object into a string, containing the book code, title and text of the law.

    Args:
        law: A Law object.

    Returns:
        A string containing the book code, title and text of the law.
    """
    text = f"""\
Gesetzbuch: {law.book_code}
Gesetz: {law.title} 
Gesetzestext:
{law.text}
"""
    return text


def rewrite_law_text(text: str, view: str) -> str:
    """Rewrite a law text from the given perspective.

    This function takes a law text and a perspective as input, and returns a new law text that is
    rewritten from the given perspective.

    Args:
        text: The original law text. This is the text that will be rewritten.
        view: The perspective to rewrite the text from. This can be any perspective, such as a
            summary, a translation for people with low german language skills, or a
            paraphrased version of the text.

    Returns:
        The rewritten law text. This is the text that has been rewritten from the given
        perspective.

    Raises:
        Exception: If there is an error creating the OpenAI client, or if there is an error
            making the request to the OpenAI API.
    """

    # Check if the OpenAI API key has been set
    openai_key = os.getenv("OPENAI_API_KEY")

    if not openai_key:
        logging.info("No OpenAI API key found")
        raise Exception("No OpenAI API key found")
        # return ""
    
    try:
        # Create the OpenAI client
        openai_client = OpenAI(api_key=openai_key)
    except Exception as e:
        # Log any errors that occur while creating the client
        logging.error(f"Failed to create OpenAI client: {e}")
        raise Exception("Failed to create OpenAI client")
        # return ""


    # Create the prompt for the AI model
    prompt_system = f"""\
Du bist ein erfahrener Anwalt. 
Deine Aufgabe ist es, basierend auf einem deutschen Gesetzestext <gesetz></gesetz>, einen neuen text zu formulieren.
Dieser text muss der in <perspektive></perspektive> beschriebenen Perspektive entprechen.
Diese Perspektive könnte alles mögliche sein.
Sie könnte es z.B. verlangen den Text einfach nur zusammenzufassen, oder aber auch
eine Frage eines naiven Twitter Users umzuformulieren.
Wichtig ist, dass unabhängig von der Perspektive viele wichtigen Informationen und Keywords des Gesetzes enthalten sind.
Der Kontext ist auch sehr relevant. Aus welchem Gesetzbuch ein Text z.B. kommt, kann dessen Bedeutung stark verändern.
Achte darauf, dass der Kontext erhalten bleibt, ohne ihn direkt zu zitieren.
Unabhängig von der Perspektive und dem Requirement Bedeutung und kontext zu erhalten, sollte die umformulierte Form nicht sehr sein.
Gib nur das aus der neuen Perspektive umformulierte Gesetzt zurück, sonst nichts!
"""

    prompt = f"""\
<gesetz>
{text}
</gesetz>

<perspektive>
{view}
</perspektive>
"""
  
    # Try to make the request to the OpenAI API. Retry multiple times if there is an error
    max_tries = 1
    while max_tries > 0:
        max_tries -= 1
        try:
            # Make the request to the OpenAI API
            responses = openai_client.chat.completions.create(
                model = "gpt-4o-mini",
                messages = [{"role": "system", "content": prompt_system}, {"role": "user", "content": prompt}],
                temperature = 0.5,
                max_tokens = 2048,
            )

            message = responses.choices[0].message

            # Check if there was an error in the response
            if not message.content:
                logging.info("No content found in response")
            elif message.refusal:
                logging.error("Refusal: ", message.refusal)
            else:
                # Print and return the rewritten text
                print("Content: ", message.content)
                return message.content
        
        except Exception as e:
            # Log any errors that occur
            logging.error("Failed to generate keywords: ", e)

    # If no rewritten text was found, return the original text
    return text



def enrich_law_text(text: str) -> str:
    """
    Enriches a given law text by rewriting it from different perspectives.

    Args:
        text: The original law text that should be enriched.

    Returns:
        A new string containing the original text, and the rewritten versions of the text.
        Each rewritten text is separated by 3 newlines.

    """
    views = [
        "Zusammenfassung in professioneller Sprache",
        "Zusammenfassung für Menschen mit geringer deutscher Sprachkentniss",
        "Drei Fragen, die unterschiedliche Twitter Nutzer zu diesem Gesetzt stellen könnten. Nur die Fragen, keine Antworten."
    ]

    texts = [rewrite_law_text(text, view) for view in views]

    # Join original text with rewritten versions, separated by 3 newlines
    enriched_text = text + '\n\n\n' + '\n\n\n'.join(texts)

    return enriched_text

def delete_random_paragraph(text: str) -> str:
    """
    Deletes a random paragraph from the given text.

    This function splits the given text into paragraphs by two or more newlines, then
    randomly selects one of the paragraphs to remove. The remaining paragraphs are then
    joined back together with two newlines, and the new text is returned.

    Args:
        text: The text to delete a random paragraph from.

    Returns:
        The text with a random paragraph removed.
    """
    # Split the text into paragraphs by two or more newlines
    paragraphs = text.split('\n\n')
    
    # If there's only one or no paragraphs, return the text unchanged
    if len(paragraphs) <= 1:
        # This is the simplest case, where there's only one or no paragraphs.
        # In this case, we can just return the text unchanged.
        return text
    
    # Randomly select a paragraph to remove
    paragraphs.pop(random.randint(0, len(paragraphs) - 1))
    
    # Join the remaining paragraphs back together with two newlines
    # This will create the new text, which we will return.
    return '\n\n'.join(paragraphs)


# def limit_text_length(text: str) -> str:
#     """
#     Limits the length of a given text by removing random paragraphs until the text length is 8191 or less.

#     Args:
#         text (str): The text to be limited in length.

#     Returns:
#         str: The text with its length limited to 8191 or less.
#     """
#     new_text = text
#     while len(new_text) > 8191:
#         new_text = delete_random_paragraph(new_text)
#     return new_text


def law_to_embedding_text(law: Law) -> str:
    """
    Converts a given Law object to a string that can be used as input for a language model.

    Args:
        law (Law): The Law object to be converted.

    Returns:
        str: A string containing the book code, title and text of the law, as well as enriched versions of the text for better understanding.
    """
    # Convert the Law object to a string, containing the book code, title and text of the law
    text = law_to_text(law)

    # Enrich the text by adding different perspectives to it
    enriched_text = enrich_law_text(text)

    # Return the enriched text
    return enriched_text


def embed_text_recursive(text: str, tokenizer: tiktoken.Encoding, max_tokens: int, dims: int, openai_client: OpenAI) -> np.ndarray:
    """
    Recursively embeds the given text into a numerical representation using the OpenAI API.

    Args:
        text (str): The input text to be embedded.
        tokenizer (tiktoken.Encoding): The tokenizer used to encode the input text.
        max_tokens (int): The maximum number of tokens allowed in the input text.
        dims (int): The dimensionality of the embedding.
        openai_client (OpenAI): The OpenAI client used to generate the embedding.

    Returns:
        np.ndarray: The embedded text as a numerical representation.
    """

    # If the text exceeds the maximum token limit, split it recursively
    if len(tokenizer.encode(text)) > max_tokens:
        # Split the text by lines, respecting line breaks
        lines = text.splitlines()
        mid_point = len(lines) // 2
        
        # Recursively embed the first and second halves
        first_half = embed_text("\n".join(lines[:mid_point]))
        second_half = embed_text("\n".join(lines[mid_point:]))
        
        # Average the embeddings from both halves
        return np.mean([first_half, second_half], axis=0)

    # Generate embedding for the text using OpenAI API
    try:
        response = openai_client.embeddings.create(input=[text], model=os.getenv("EMBEDDING_MODEL"))
        embedding = np.array(response.data[0].embedding, dtype=np.float32)
        return embedding
    except Exception as e:
        logging.error(f"Failed to embed text section: {e}")
        return np.zeros(dims, dtype=np.float32) 
    
    
def embed_text(text: str) -> np.ndarray:
    """
    Embeds the given text into a numerical representation using the OpenAI API.

    Args:
        text (str): The input text to be embedded.

    Returns:
        np.ndarray: The embedded text as a numerical representation.
    """
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    tokenizer = tiktoken.get_encoding(os.getenv("EMBEDDING_MODEL_TOKENIZER"))
    max_tokens = int(os.getenv("EMBEDDING_MODEL_MAX_TOKENS", 8191))
    dims = int(os.getenv("EMBEDDING_MODEL_DIMS", 1536))

    return embed_text_recursive(text, tokenizer, max_tokens, dims, openai_client)


def embedding_to_blob(embedding: np.ndarray) -> bytes:
    """
    Converts a given numerical embedding into a byte representation.

    Args:
        embedding (np.ndarray): The numerical embedding to be converted.

    Returns:
        bytes: The byte representation of the embedding.
    """
    return embedding.tobytes()


def blob_to_embedding(blob: bytes) -> np.ndarray:
    """
    Converts a given byte representation into a numerical embedding.

    Args:
        blob (bytes): The byte representation of the embedding.

    Returns:
        np.ndarray: The numerical embedding.
    """
    return np.frombuffer(blob, dtype=np.float32)


def processed_law(law: Law) -> EmbeddedLaw:
    """
    This function processes a given law object and returns a ProcessedLaw object.
    
    It extracts the law's id, book code, title, text, and source URL, and then 
    generates a reduced text representation and various embedding representations.
    
    Args:
        law (Law): The law object to be processed.
    
    Returns:
        ProcessedLaw: The processed law object.
    """
    law_id = law.id
    book_code = law.book_code
    title = law.title
    text = law.text
    source_url = law.source_url

    text_reduced = text[:EmbeddedLaw.reduced_text_length]
    embedding_text = law_to_embedding_text(law)
    embedding_base = embedding_to_blob(embed_text(embedding_text))
    embedding_optimized = embedding_base

    processed_law = EmbeddedLaw(
        law_id = law_id,
        book_code = book_code,
        title = title,
        text = text,
        source_url = source_url,
        text_reduced = text_reduced,
        embedding_text = embedding_text,
        embedding_base = embedding_base,
        embedding_optimized = embedding_optimized
    )
    return processed_law



def migrate_laws() -> None:
    """
    Migrates all laws in the Law table to the ProcessedLaw table.

    Laws are migrated by extracting the relevant fields from the Law object and
    generating a reduced text representation and various embedding representations.
    The resulting ProcessedLaw object is then created in the database.

    Args:
        None

    Returns:
        None
    """

    logging.info("Starting law migration")
    # Get all laws, that are not in the ProcessedLaw table based on the id and law_id
    laws_to_migrate: List[Law] = Law.objects.all().exclude(id__in=EmbeddedLaw.objects.values_list('law_id', flat=True))
    migrated_laws = []

    # Iterate over the laws and process them
    for law in laws_to_migrate:
        # Process the law and create a ProcessedLaw object
        migrated_laws.append(processed_law(law)) 

    try:
        # Create the ProcessedLaw objects in the database
        EmbeddedLaw.objects.bulk_create(migrated_laws)
        # Log how many laws were created in the database
        logging.info(f"Created {len(migrated_laws)} laws in the database")
    except IntegrityError:
        # Log an error if there was a problem creating the laws in the database
        logging.error("Failed to create laws in the database")




def remigrate_all_laws():
    pass


def start_migration_task():
    lock_name = 'law_migration_lock'

    if Lock.acquire_lock(lock_name):
        try:
            # Start the background task in a separate thread
            threading.Thread(target=migrate_laws, daemon=True).start()
            return JsonResponse({'status': 'Task started'}, status=202)
        except Exception as e:
            return JsonResponse({'status': 'Task failed', 'error': str(e)}, status=500)
        finally:
            Lock.release_lock(lock_name)
    else:
        return JsonResponse({'status': 'Task is already running'}, status=202)