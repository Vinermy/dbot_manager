import uuid

import django.db
import openpyxl

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


# Create your models here.
class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    can_edit_parts = models.BooleanField(default=False)
    can_edit_bots = models.BooleanField(default=False)



class Profile(AbstractUser):
    role = models.ForeignKey(to=Role, on_delete=models.SET_NULL, default=None, null=True, related_name='profiles')

    def can_edit_roles(self) -> bool:
        return self.is_staff

    def can_edit_profiles(self) -> bool:
        return self.is_staff

    def can_edit_parts(self) -> bool:
        return self.is_staff or self.role.can_edit_parts

    def can_edit_bots(self) -> bool:
        return self.is_staff or self.role.can_edit_bots


class DBotPartKind(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512)


class DBotPart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512, default='')
    vendor_code = models.CharField(max_length=20, unique=True)
    kind = models.ForeignKey(to=DBotPartKind, on_delete=models.SET_NULL, related_name='parts', null=True)
    weight = models.IntegerField(validators=[MinValueValidator(0)])
    manufacture_date = models.DateField()

def load_parts_from_file(file):
    workbook: openpyxl.Workbook = openpyxl.load_workbook(file)
    sheet = workbook.worksheets[0]
    for row in sheet.iter_rows(min_row=2, min_col=1, max_col=5):
        name = row[0].value
        vendor_code = row[1].value
        kind_name = row[2].value
        weight = row[3].value * 1000
        manufacture_date = row[4].value

        kind, created = DBotPartKind.objects.get_or_create(
            name=kind_name
        )
        try:
            DBotPart.objects.create(
                name=name,
                vendor_code=vendor_code,
                kind=kind,
                weight=weight,
                manufacture_date=manufacture_date,
            )
        except django.db.IntegrityError:
            pass

class DBot(models.Model):
    STATE_CHOICES = [
        ('DS', 'Проектируется'),
        ('MN', 'В серийном производстве'),
        ('DC', 'Снят с производства'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512, default="")
    vendor_code = models.CharField(max_length=20, unique=True)
    state = models.CharField(max_length=2, choices=STATE_CHOICES, default='DS')
    parts = models.ManyToManyField(to=DBotPart, related_name='bots')
    price = models.DecimalField(decimal_places=2, validators=[MinValueValidator(0.0)], default=0.0, max_digits=10)

    def weight_kg(self) -> float:
        return sum(self.parts.values_list('weight', flat=True).all()) / 1000

    def is_sellable(self) -> bool:
        return self.state == 'MN'

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(to=Profile, on_delete=models.SET_NULL, null=True, related_name='comments')
    launch_process = models.ForeignKey(to='LaunchProcess', on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now=True, null=True)

class LaunchStage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512)
    previous_stage = models.OneToOneField(to='LaunchStage', on_delete=models.SET_NULL, null=True,
                                          related_name='next_stage', unique=True)
    responsible_role = models.ForeignKey(to=Role, on_delete=models.SET_NULL, null=True,
                                         related_name='stages_responsible')
    requires_parts_access = models.BooleanField(default=False)


class LaunchProcess(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bot = models.OneToOneField(to=DBot, on_delete=models.CASCADE, related_name='launch_process')
    stage = models.ForeignKey(to=LaunchStage, on_delete=models.SET_NULL, null=True, related_name='processes')
    is_finished = models.BooleanField(default=False)
