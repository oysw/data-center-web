from django.db import models
# Create your models here.


class Job(models.Model):
    STATUS = (
        ('F', 'Finished'),
        ('W', 'Waiting'),
        ('E', 'Error'),
        ('I', 'Idle'),
        ('P', 'Process'),
        ('C', 'Calculating'),
    )
    owner = models.CharField(max_length=150)
    label = models.CharField(max_length=30)
    raw = models.FileField(blank=True, upload_to='raw/')
    mod = models.FileField(blank=True, upload_to='model/')
    upload = models.FileField(blank=True, upload_to='upload/')
    create_time = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, default='I', choices=STATUS)

    def __int__(self):
        return self.id
