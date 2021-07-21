from django.db import models

class ImageSaver(models.Model):
    candidate_image = models.ImageField(upload_to='images',null = True,blank = True)
    
    def __str__(self):
        return str(self.candidate_image.name)