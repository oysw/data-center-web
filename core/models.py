from django.db import models
# Create your models here.


class Job(models.Model):
    STATUS = (
        ('F', 'Finished'),
        ('W', 'Waiting'),
        ('E', 'Error'),
        ('C', 'Calculating'),
    )
    owner = models.CharField(max_length=150)
    csv_data = models.FileField(blank=True, upload_to='raw/')
    mod = models.FileField(blank=True, upload_to='result/')
    create_time = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, default='W', choices=STATUS)

    def __str__(self):
        return self.owner
