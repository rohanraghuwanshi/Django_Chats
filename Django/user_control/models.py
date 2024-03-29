from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)

# Create your models here.
class CustomUserManager(BaseUserManager):
    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("Username field is required")

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff = True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser = True.")

        return self._create_user(username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(unique=True, max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "username"
    objects = CustomUserManager()

    def __str__(self):
        return self.username

    class Meta:
        ordering = ("created_at",)


class UserProfile(models.Model):

    user = models.OneToOneField(
        CustomUser, related_name="user_profile", on_delete=models.CASCADE
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    caption = models.CharField(max_length=250, blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="user/profile_picture", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return self.user.username


class JWT(models.Model):
    user = models.OneToOneField(
        CustomUser, related_name="login_user", on_delete=models.CASCADE
    )
    access = models.TextField()
    refresh = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
