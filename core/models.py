from django.db import models
from django.core.files.storage import FileSystemStorage
# Create your models here.

fs = FileSystemStorage(location='/tmp/ai4chem/')


class Job(models.Model):
    STATUS = (
        ('F', 'Finished'),
        ('W', 'Waiting'),
        ('E', 'Error'),
        ('C', 'Calculating'),
    )
    owner = models.CharField(max_length=150)
    x_file = models.FileField(blank=True, storage=fs)
    y_file = models.FileField(blank=True, storage=fs)
    best = models.CharField(max_length=200, blank=True)
    image = models.ImageField(blank=True, storage=fs)
    trials = models.FileField(blank=True, storage=fs)
    create_time = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, default='W', choices=STATUS)

    def __str__(self):
        return self.owner
