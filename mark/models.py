from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Status(models.Model):
    status = models.CharField(max_length=10)  #I can add unique = True

    def __str__(self):
        return f"{self.status}"

class Date(models.Model):
    date = models.DateField()  #I can add unique = True

    def __str__(self):
        return f"{self.date}"

class Course(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user}: {self.course}"

class Attend(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  date = models.ForeignKey(Date, on_delete=models.CASCADE, related_name="mark_date")
  status = models.ForeignKey(Status, on_delete=models.CASCADE, related_name="mark_status")
  course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="course_add", null=True) #nul==false after testing

  def __str__(self):
        return f"{self.user.username} - {self.date} - {self.course} - {self.status} "
  
