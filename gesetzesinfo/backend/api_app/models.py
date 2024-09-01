from django.db import models

# Create your models here.



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




class Law(models.Model):

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

    source_url = models.TextField(default='')

    # When was the entry created or last edited
    last_updated = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.title}"
    

    class Meta:
        # Additional options for the model
        verbose_name = "Law"
        verbose_name_plural = "Laws"




class ProccessedLaw(models.Model):

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

    # What law this definition comes from
    source_url = models.TextField(default='')

    # When was the entry created or last edited
    last_updated = models.DateTimeField(auto_now=True)


    # Embedding stuff
    # 
    embedding_text = models.TextField(default='')

    #
    embedding_base = models.BinaryField(default=None)

    # 
    embedding_optimized = models.BinaryField(default=None)



    def __str__(self):
        return f"{self.title}"
    

    class Meta:
        # Additional options for the model
        verbose_name = "Law"
        verbose_name_plural = "Laws"


class LawWordDefinition(models.Model):

    # Main Key
    id = models.AutoField(primary_key=True)

    # What law this definition belongs to
    law = models.ForeignKey(Law, on_delete=models.CASCADE)

    word = models.CharField(max_length=128)

    definition = models.TextField()

    def __str__(self):
        return f"{self.word} ({self.law.title})"
    
    
    

