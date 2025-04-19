from django.contrib import admin
from .models import JobTitle, Keyword, UploadedFile

# Register your models here.
admin.site.register(JobTitle)
admin.site.register(Keyword)
admin.site.register(UploadedFile)