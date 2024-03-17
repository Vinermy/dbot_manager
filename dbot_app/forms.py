from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from . import models
from .models import DBotPartKind

class BetterChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class SignupForm(UserCreationForm):
    password1 = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Минимум 8 символов. Минимум 1 буква или специальный символ',
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text='Совпадает с паролем',
    )
    class Meta:
        model = models.Profile
        fields = ('first_name', 'last_name', 'username', 'email',)
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'username': 'Логин',
            'email': 'E-mail',
        }
        help_texts = {
            'first_name': '',
            'last_name': '',
            'username': 'Не более 150 символов. Может содержать только латинские буквы, цифры и символы из набора @/./+/-/_',
            'email': 'Должен быть действительным адресом электронной почты',
        }


class SigninForm(forms.Form):
    username = forms.CharField(label='Логин')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')



class RoleForm(forms.ModelForm):
    class Meta:
        model = models.Role
        fields = ('name', 'can_edit_parts', 'can_edit_bots', 'can_start_process',)
        labels = {
            'name': 'Название',
            'can_edit_parts': 'Имеет доступ к редактированию деталей',
            'can_edit_bots': 'Имеет доступ к редактированию роботов',
            'can_start_process': 'Может начать бизнес-процесс',
        }


class PartForm(forms.ModelForm):
    kind = BetterChoiceField(queryset=DBotPartKind.objects.all(), label='', required=True, empty_label=None,
                             widget=forms.Select(attrs={'class': 'form-input'}))
    class Meta:
        model = models.DBotPart
        fields = ('name', 'vendor_code', 'manufacture_date', 'weight')
        labels = {
            'name': 'Название',
            'vendor_code': 'Артикул',
            'manufacture_date': 'Дата изготовления',
            'weight': 'Вес в граммах',
        }

class UploadFileForm(forms.Form):
    parts = forms.FileField(
        widget=forms.FileInput(attrs={'accept': '.xlsx'}),
        label='Файл с деталями',
        help_text='Загрузите файл в формате .xlsx'
    )