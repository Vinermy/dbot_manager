from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import render, redirect
from . import forms
from .forms import SignupForm
from .models import Role, Profile


# Create your views here.

@login_required(login_url='signin')
def home(request):
    return render(request, 'home.html')


def signup(request):
    if request.method == 'POST':
        form = forms.SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.save()
            login(request, user, backend='axes.backends.AxesBackend')
            return redirect('home')
    else:
        form = forms.SignupForm()
    return render(request, 'auth/signup.html', {'form': form})


def signin(request):
    if request.method == 'POST':
        form = forms.SigninForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['username'], password=cd['password'], request=request)
            if user is not None:
                if user.is_active:
                    login(request, user, backend='axes.backends.AxesBackend')
                    return redirect('home')
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    else:
        form = forms.SigninForm()
    return render(request, 'auth/signin.html', {'form': form})


@login_required(login_url='signin')
@user_passes_test(lambda u: u.can_edit_roles())
def manage_roles(request):
    if request.method == 'POST':
        form = forms.RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            return redirect('manage_roles')
    else:
        form = forms.RoleForm()

    ctx = {
        'form': form,
        'roles': Role.objects.all(),
    }
    return render(request, 'manage/roles.html', ctx)


def log_out(request):
    logout(request)
    return redirect('signin')


@login_required(login_url='signin')
@user_passes_test(lambda u: u.can_edit_profiles())
def manage_accounts(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = Role.objects.get(id=request.POST['role'])
            user.save()
            return redirect('manage_accounts')

    ctx = {
        'admins': Profile.objects.filter(is_staff=True),
        'plebs': Profile.objects.filter(is_staff=False),
        'form': forms.SignupForm(),
        'roles': Role.objects.all()
    }
    return render(request, 'manage/accounts.html', ctx)
