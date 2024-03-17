import datetime
import random
from pathlib import Path

import axes.models
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from fpdf.fpdf import FPDF

from . import forms
from .forms import SignupForm, UploadFileForm, PartForm
from .models import Role, Profile, LaunchStage, DBot, LaunchProcess, DBotPart, DBotPartKind, load_parts_from_file, \
    Comment
from .pdf import PriceList


def permission_required(test):
    def actual_decorator(func):
        def wrapper(request, *args, **kwargs):
            if test(request.user):
                return func(request, *args, **kwargs)
            else:
                return redirect('unauthorized')
        return wrapper

    return actual_decorator


# Create your views here.

@login_required(login_url='signin')
def home(request):
    ctx = {
        'processes': LaunchProcess.objects.count(),
        'parts': DBotPart.objects.count(),
        'bots': DBot.objects.count(),
    }
    return render(request, 'home.html', ctx)


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
            print(form.data)
            print(form.error_messages)
            print([(field.name, field.errors, '\n') for field in form])
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
                    return redirect('disabled_account')
            else:
                return redirect('invalid_credentials')
    else:
        form = forms.SigninForm()
    return render(request, 'auth/signin.html', {'form': form})


@login_required(login_url='signin')
@permission_required(lambda u: u.can_edit_roles())
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
@permission_required(lambda u: u.can_edit_profiles())
def manage_accounts(request):
    form = SignupForm()
    if request.method == 'POST':
        match request.POST['form-kind']:
            case 'create-account':
                form = SignupForm(request.POST)
                if form.is_valid():
                    user = form.save(commit=False)
                    user.role = Role.objects.get(id=request.POST['role'])
                    user.save()
            case 'account-actions':
                account = Profile.objects.get(id=request.POST['account-id'])
                match request.POST['action']:
                    case 'activate':
                        account.is_active = True
                    case 'deactivate':
                        account.is_active = False
                account.save()
        return redirect('manage_accounts')

    ctx = {
        'admins': Profile.objects.filter(is_staff=True),
        'plebs': Profile.objects.filter(is_staff=False),
        'form': form,
        'roles': Role.objects.all()
    }
    return render(request, 'manage/accounts.html', ctx)


@login_required(login_url='signin')
@permission_required(lambda u: u.is_staff)
def admin_menu(request):
    if request.method == 'POST':
        data = request.POST
        match data['form-type']:
            case 'add-stage':
                name = data['name']
                role = Role.objects.get(id=data['role'])
                prev_stage = LaunchStage.objects.get(id=data['prev_stage']) if data['prev_stage'] != "None" else None

                stage = LaunchStage(
                    name=name,
                    previous_stage=prev_stage,
                    responsible_role=role,
                )
                stage.save()
                return redirect('admin_menu')
            case _:
                pass

    ctx = {
        'last_logins': axes.models.AccessLog.objects.order_by('-attempt_time').all()[:5:],
        'roles': Role.objects.all(),
        'stages': LaunchStage.objects.all(),
    }
    return render(request, 'admin_menu.html', ctx)


@login_required(login_url='signin')
@permission_required(lambda u: u.is_staff)
def auth_logs(request):
    ctx = {
        'logins': axes.models.AccessLog.objects.order_by('-attempt_time').all(),
    }
    return render(request, 'logs/auth.html', ctx)


def processes_main(request):
    ctx = {
        'processes': LaunchProcess.objects.all()
    }
    return render(request, 'processes/main.html', ctx)

@login_required(login_url='signin')
@permission_required(lambda u: u.can_start_process())
def processes_new(request):
    if request.method == 'POST':
        data = request.POST
        bot_name = data['name']
        vendor_code = "BOT-" + ''.join(random.choice('0123456789') for _ in range(16))
        bot = DBot(
            name=bot_name,
            vendor_code=vendor_code,
        )
        bot.save()
        process = LaunchProcess(
            bot=bot,
            stage=LaunchStage.objects.filter(previous_stage=None).first(),
        )
        process.save()
        return redirect('processes_main')
    return render(request, 'processes/new.html')

@login_required(login_url='signin')
def process(request, pk):
    if request.method == 'POST':
        data = request.POST
        match data['form-kind']:
            case 'add-part-to-bot':
                part = DBotPart.objects.get(vendor_code=data['part'])
                bot = DBot.objects.get(launch_process__id=pk)
                bot.parts.add(part)
            case 'add-comment':
                author = request.user
                text = data['comment']
                Comment.objects.create(
                    author=author,
                    text=text,
                    launch_process_id=pk,
                )
            case 'actions':
                action = data['action']
                process = LaunchProcess.objects.get(id=pk)
                match action:
                    case 'advance':
                        if process.stage.next_stage is not None:
                            process.stage = process.stage.next_stage
                            process.save()
                            process.comments.add(Comment.objects.create(
                                author=None,
                                text=f"{request.user.get_full_name()} продвинул проект на следующую стадию - {process.stage.name}",
                                launch_process_id=pk
                            ))
                    case 'revert':
                        if process.stage.previous_stage is not None:
                            process.stage = process.stage.previous_stage
                            process.save()
                            process.comments.add(Comment.objects.create(
                                author=None,
                                text=f"{request.user.get_full_name()} вернул проект на стадию {process.stage.name}",
                                launch_process_id=pk,
                            ))
                    case 'finish':
                        bot = process.bot
                        bot.state = 'MN'
                        bot.save()
                        process.is_finished = True
                        process.save()
                        process.comments.add(Comment.objects.create(
                            author=None,
                            text=f"{request.user.get_full_name()} завершил бизнес-процесс",
                            launch_process_id=pk,
                        ))
            case 'set-price':
                price = data['price']
                bot = LaunchProcess.objects.get(id=pk).bot
                bot.price = price
                bot.save()

        return redirect('process', pk)

    ctx = {
        'process': LaunchProcess.objects.get(id=pk),
        'stages': LaunchStage.objects.all(),
        'parts': DBotPart.objects.all(),
        'comments': Comment.objects.filter(launch_process_id=pk).order_by('-timestamp').all(),
    }
    return render(request, 'processes/view.html', ctx)


@login_required(login_url='signin')
@user_passes_test(lambda u: u.can_edit_parts, login_url='signin')
def manage_parts(request: HttpRequest):
    if request.method == 'POST':
        data = request.POST
        match data['form-kind']:
            case 'add-part-kind':
                kind = DBotPartKind(
                    name=data['name'],
                )
                kind.save()
                return redirect('parts')

            case 'remove-kind':
                kind = DBotPartKind.objects.get(id=data['kind-id'])
                kind.delete()
                return redirect('parts')

            case 'add-part-file':
                form = UploadFileForm(request.POST, request.FILES)
                if form.is_valid():
                    handle_uploaded_file(request.FILES['parts'])
                return redirect('parts')

            case 'add-part':
                form = PartForm(request.POST)
                if form.is_valid():
                    part = form.save(commit=False)
                    part.kind = form.cleaned_data['kind']
                    part.save()
                return redirect('parts')

    ctx = {
        'parts': DBotPart.objects.all(),
        'kinds': DBotPartKind.objects.all(),
        'file_form': UploadFileForm(),
        'part_form': PartForm(),
    }
    return render(request, 'manage/parts.html', ctx)


def handle_uploaded_file(f):
    with open("temp.xlsx", "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    load_parts_from_file("temp.xlsx")


def bots(request):
    if request.method == 'POST':
        data = request.POST
        bot = DBot.objects.get(id=data['bot-id'])
        bot.state = 'DC'
        bot.save()
        return redirect('bots')

    ctx = {
        'bots': DBot.objects.all(),
    }
    return render(request, 'bots.html', ctx)


def generate_price_list(request):
    bots = DBot.objects.filter(state='MN').order_by('-price').values_list('vendor_code', 'name', 'price')

    row = "<tr><td>{}</td><td>{}</td><td>{}</td></tr>"

    html = ("<table>"
            "<thead>"
            "<tr>"
            "<th>Артикул</th>"
            "<th>Название</th>"
            "<th>Цена</th>"
            "</tr>"
            "</thead>"
            "{}"
            "</table>").format('\n'.join(row.format(code, name, price) for (code, name, price) in bots))

    doc = PriceList()
    doc.add_page()
    doc.write_html(html)
    doc.output("output.pdf")

    with open("output.pdf", 'rb') as pdf:
        contents = pdf.read()

    response = HttpResponse(
        contents,
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f'attachment; filename="price_list.pdf"'
        },

    )
    return response


def unauthorized(request):
    return render(request, 'auth/unauthorized.html')


def disabled_account(request):
    return render(request, 'auth/disabled.html')


def invalid_credentials(request):
    return render(request, 'auth/invalid_credentials.html')