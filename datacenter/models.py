from django.db import models

# Create your models here.

# class User(models.Model):
#     name = models.CharField(max_length=20)
#     phone = models.CharField(max_length=20, primary_key=True)
#     qq = models.CharField(max_length=20)
#     email = models.EmailField()
#
#     def __unicode__(self):
#         return self.name
#
# class File(models.Model):
#     owner = models.ForeignKey(User, related_name='owner_phone', on_delete=models.CASCADE)
#     upload_time = models.DateTimeField()
#     status = models.BooleanField()
#
#     def __unicode__(self):
#         return self.upload_time
