from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from . import models


class SignupForm(UserCreationForm):
    password1 = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='',
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text='',
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

class SigninForm(forms.Form):
    username = forms.CharField(label='Логин')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')



class RoleForm(forms.ModelForm):
    class Meta:
        model = models.Role
        fields = ('name',)
        labels = {
            'name': 'Название'
        }