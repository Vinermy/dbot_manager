import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)

class Profile(AbstractUser):
    role = models.ForeignKey(to=Role, on_delete=models.SET_NULL, default=None, null=True, related_name='profiles')

    def can_edit_roles(self) -> bool:
        return self.is_staff

    def can_edit_profiles(self) -> bool:
        return self.is_staff