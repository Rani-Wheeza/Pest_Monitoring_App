"""Application user (Task 5: UserAccount). Passwords are handled by Entra ID."""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = "User"
        WORKER = "Worker"
        PEST_CONTROL_EXPERT = "PestControlExpert"
        SURVEYOR = "Surveyor"
        ADMIN = "Admin"

    entra_object_id = models.UUIDField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    postcode = models.CharField(max_length=10, blank=True)
    district = models.ForeignKey("reference.District", null=True, blank=True, on_delete=models.SET_NULL)
    consent_to_updates = models.BooleanField(default=False)

    class Meta:
        db_table = "UserAccount"

    def __str__(self) -> str:
        return self.email or self.username

    @property
    def is_worker(self) -> bool:
        return self.role in (self.Role.WORKER, self.Role.ADMIN)
