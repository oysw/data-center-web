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
    x_file = models.FileField(blank=True, upload_to='calc_file/')
    y_file = models.FileField(blank=True, upload_to='calc_file/')
    best = models.CharField(max_length=200, blank=True)
    image = models.ImageField(blank=True, upload_to='result_file/')
    trials = models.FileField(blank=True, upload_to='result_file/')
    create_time = models.DateTimeField(editable=True, auto_now=True)
    status = models.CharField(max_length=10, default='W', choices=STATUS)

    def __str__(self):
        return self.owner
