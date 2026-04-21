# Model of account

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, tu_id, **extra_fields):
        if not tu_id:
            raise ValueError("The TU ID must be set")

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        user = self.model(tu_id=tu_id, **extra_fields)

        password = extra_fields.pop('password', None)
        if password:
            user.set_password(password)
            
        user.save(using=self._db)
        return user

    def create_superuser(self, tu_id, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'Admin') 

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(tu_id, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    tu_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    ROLE_CHOICES = [
        ('Student', 'นักศึกษา'),
        ('Lecturer', 'อาจารย์'),
        ('Admin', 'ผู้ดูแลระบบ'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Student')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) 

    objects = UserManager()

    USERNAME_FIELD = 'tu_id'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.tu_id} - {self.first_name}"