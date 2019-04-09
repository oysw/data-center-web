from django.db import models
from django.core.files.storage import FileSystemStorage

# Create your models here.

fs_cal = FileSystemStorage(location='/tmp/ai4chem/media/cal_file')
fs_res = FileSystemStorage(location='/tmp/ai4chem/media/result')

class Job(models.Model):
    JOB_STATUS = (
        ('C', 'Complete'),
        ('P', 'Processing'),
        ('W', 'Waiting'),
        ('E', 'Error'),
    )
    owner = models.CharField(max_length=150)
    x_file = models.FileField(storage=fs_cal)
    y_file = models.FileField(storage=fs_cal)
    create_time = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=JOB_STATUS)
    result = models.FileField(default=False, storage=fs_res)

    def __str__(self):
        return self.owner
