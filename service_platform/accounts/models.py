from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import random


class UserManager(BaseUserManager):
    """Custom manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        from profiles.models import NormalUserProfile, StaffProfile

        if user.role == User.Role.NORMAL:
            NormalUserProfile.objects.get_or_create(user=user)
        elif user.role in {User.Role.STAFF, User.Role.SUPER_ADMIN}:
            StaffProfile.objects.get_or_create(user=user)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # Super admin is always verified and approved
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)
        extra_fields.setdefault('is_approved', True)
        extra_fields.setdefault('role', User.Role.SUPER_ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model supporting 3 roles: Super Admin, Staff, Normal."""

    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        STAFF = 'staff', 'Staff User'
        NORMAL = 'normal', 'Normal User'

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.NORMAL)

    # Account states
    is_active = models.BooleanField(default=False)   # only active after email verification
    is_staff = models.BooleanField(default=False)    # Django admin access
    is_email_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False) # For Staff: needs Super Admin approval
    is_blocked = models.BooleanField(default=False)  # Admin block

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_staff_user(self):
        return self.role == self.Role.STAFF

    @property
    def is_normal_user(self):
        return self.role == self.Role.NORMAL


class EmailVerification(models.Model):
    """Stores 6-digit email verification code per user."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def regenerate(self):
        self.code = f"{random.randint(100000, 999999)}"
        self.is_used = False
        self.save()
        return self.code