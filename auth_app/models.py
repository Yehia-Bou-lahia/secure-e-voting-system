from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

USER_ROLES = (
    ('student', 'Student',),
    ('candidate', 'Candidate')
)


# Create your models here.
class User(AbstractUser):
    """
    User model
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="User identifier"
    )
    email = models.EmailField(verbose_name="Email Address", unique=True)
    role = models.CharField(max_length=10, choices=USER_ROLES, default='student')
    created_at = models.DateTimeField(verbose_name='Created At', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Updated At', auto_now=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        """ String representation """
        return f"{self.username}: {str(self.email)}"


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    profile_picture = models.ImageField(verbose_name='Profile picture', blank=True, null=True,
                                        upload_to='profile_pictures/')
    name = models.CharField(max_length=100, verbose_name="Student Name")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name='Created At', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Updated At', auto_now=True)

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self) -> str:
        return f"{self.name}"


class Candidate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    profile_picture = models.ImageField(verbose_name='Profile picture', blank=True, null=True,
                                        upload_to='profile_pictures/')
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name='Created At', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Updated At', auto_now=True)
