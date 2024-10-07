import os
import sqlite3
from django.db import models
from django.utils import timezone
import numpy as np
from django_project import settings


#########################################################
#                                                       #
#                MODELS - Database Schema               #
#                                                       #
#########################################################


class Lock(models.Model):
    """
    A model representing a lock mechanism for synchronization purposes.

    This class provides a way to create, acquire, and release locks,
    which can be used to prevent concurrent access to shared resources.
    """

    name = models.CharField(max_length=255, unique=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        """
        Returns a string representation of the Lock instance.

        :return: The name of the lock.
        """
        return self.name

    @classmethod
    def acquire_lock(cls, lock_name, timeout=300):
        """
        Attempts to acquire a lock with the given name.

        :param lock_name: Unique name for the lock.
        :param timeout: Time in seconds to consider the lock valid (default: 300).
        :return: True if the lock was acquired, False otherwise.
        """
        now = timezone.now()
        try:
            # Try to get an existing lock or create a new one
            lock, created = cls.objects.get_or_create(name=lock_name)
            
            # Check if the lock is newly created or has timed out
            if created or (now - lock.locked_at).total_seconds() > timeout:
                # Acquire the lock
                lock.is_locked = True
                lock.locked_at = now
                lock.save()
                return True
        except cls.DoesNotExist:
            # If the lock doesn't exist, create and acquire it
            cls.objects.create(name=lock_name, is_locked=True, locked_at=now)
            return True
        
        # If we couldn't acquire the lock, return False
        return False

    @classmethod
    def release_lock(cls, lock_name):
        """
        Releases the lock with the given name.

        :param lock_name: Unique name for the lock to be released.
        """
        try:
            # Try to get the lock and release it
            lock = cls.objects.get(name=lock_name)
            lock.is_locked = False
            lock.save()
        except cls.DoesNotExist:
            # If the lock doesn't exist, do nothing
            pass


class OldTitleKeyword(models.Model):

    # Main Key
    id = models.AutoField(primary_key=True)

    keyword = models.CharField(unique=True, max_length=64)

    results = models.IntegerField(default=None)

    def __str__(self):  
        return f"Keyword: {self.keyword}, Results: {self.results}"

    class Meta:
        # Additional options for the model
        verbose_name = "Old Title Keyword"
        verbose_name_plural = "Old Title Keywords"




class OpenLegalDataLawTest(models.Model):
    id = models.AutoField(primary_key=True)
    external_id = models.IntegerField(unique=True)
    book_code = models.CharField(max_length=100)
    title = models.CharField(max_length=1024)
    text = models.TextField()
    text_char = models.CharField(max_length=1024, default='')
    
    def __str__(self):
        return self.title


class OpenLegalDataLaw(models.Model):
       # Main Key
    id = models.AutoField(primary_key=True)

    # This was the id used on the openlegaldata api
    external_id = models.IntegerField(unique=True)

    # This was the book used on the openlegaldata api
    book_code = models.CharField(max_length=100)

    # This is the title of the law
    title = models.CharField(max_length=1024)

    # This is the text of the law
    text = models.TextField(default='')
    text_char = models.CharField(max_length=1024, default='')



class Law(models.Model):

    # Main Key
    id = models.AutoField(primary_key=True)
    
    # This was the book used on the openlegaldata api
    book_code = models.CharField(max_length=100)

    # This is the title of the law
    title = models.CharField(max_length=1024)

    # This is the text of the law
    text = models.TextField(default='')

    source_url = models.TextField(default='')

    # When was the entry created or last edited
    last_updated = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.title}"
    

    class Meta:
        # Additional options for the model
        verbose_name = "Law"
        verbose_name_plural = "Laws"




class EmbeddedLaw(models.Model):

    # Main Key
    id = models.AutoField(primary_key=True)

    # This was the id used in tha Laws table
    law_id = models.IntegerField()

    # This was the book used on the openlegaldata api
    book_code = models.CharField(max_length=100)

    # This is the title of the law
    title = models.CharField(max_length=1024)

    # This is the text of the law
    text = models.TextField(default='')

    # What law this definition comes from
    source_url = models.TextField(default='')

    # When was the entry created or last edited
    last_updated = models.DateTimeField(auto_now=True)


    # Embedding 
    # Reduced version of the text, used for fast keyword search queries
    reduced_text_length = 1024
    text_reduced = models.CharField(max_length=reduced_text_length, default='')

    # Enriched version of the text, used for vector search
    embedding_text = models.TextField(default='')

    # Embedding of generated based on the embedding_text
    embedding_base = models.BinaryField(default=None)

    # Embedding that is continuously optimized through user feedback
    embedding_optimized = models.BinaryField(default=None)

    def jsonify(self):
        return {
            'Gesetzbuch': self.book_code,
            'Titel': self.title,
            'Text': self.text[:2048],
        }


    def get_as_text(self):
        return f"Gesetz: {self.title}\n\nGesetzbuch: {self.book_code}\n\nText: {self.text}"

    def get_embedding_base(self):
        return np.frombuffer(self.embedding_base, dtype=np.float32)
    
    def get_embedding_optimized(self):
        return np.frombuffer(self.embedding_optimized, dtype=np.float32)

    def __str__(self):
        return f"{self.title}"
    

    class Meta:
        # Additional options for the model
        verbose_name = "Embedded Law"
        verbose_name_plural = "Embedded Laws"

class SearchRequest(models.Model):
    reduced_text_length = 1024

    id = models.AutoField(primary_key=True)
    search_text = models.TextField(unique=True) 
    search_text_reduced = models.CharField(max_length=reduced_text_length, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.search_text}"
    
    class Meta:
        # Additional options for the model
        verbose_name = "Search Request"
        verbose_name_plural = "Search Requests"


class SearchQuery(models.Model):
    reduced_text_length = 1024

    id = models.AutoField(primary_key=True)
    search_request = models.ForeignKey(SearchRequest, on_delete=models.CASCADE, related_name='queries')
    query_text = models.TextField(default='', unique=True) 
    query_reduced = models.CharField(max_length=reduced_text_length, default='')
    embedding = models.BinaryField(default=None)

    def get_embedding(self):
        if self.embedding:
            return np.frombuffer(self.embedding, dtype=np.float32)
        else:
            raise ValueError("Embedding is None for this search query.")
        
    def __str__(self):
        return f"{self.query_text}"

    class Meta:
        # Additional options for the model
        verbose_name = "Query"
        verbose_name_plural = "Queries"



def get_law_model():
    if settings.USE_TEST_DB:
        return OpenLegalDataLawTest
    else:
        return OpenLegalDataLaw


