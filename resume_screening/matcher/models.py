from django.db import models

# Create your models here.
class JobTitle(models.Model):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title
    

class Keyword(models.Model):
    job_title = models.ForeignKey(JobTitle, on_delete=models.CASCADE, related_name='keywords')
    word = models.TextField()

    def __str__(self):
        return f"{self.word} ({self.job_title.title})"
    

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
