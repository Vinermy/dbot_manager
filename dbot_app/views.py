import datetime
import random

import axes.models
import borb.pdf as pdf
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from . import forms
from .forms import SignupForm, UploadFileForm, PartForm
from .models import Role, Profile, LaunchStage, DBot, LaunchProcess, DBotPart, DBotPartKind, load_parts_from_file, \
    Comment


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
@user_passes_test(lambda u: u.can_edit_profiles(), login_url='signin')
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


@login_required(login_url='signin')
@user_passes_test(lambda u: u.is_staff, login_url='signin')
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
@user_passes_test(lambda u: u.is_staff, login_url='signin')
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


def process(request, pk):
    if request.method == 'POST':
        data = request.POST
        match data['form-kind']:
            case 'add-part-to-bot':
                part = DBotPart.objects.get(id=data['part'])
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
    date = datetime.date.today().strftime("%d_%m")
    time = datetime.datetime.now().strftime("%H:%M")
    doc = pdf.Document()
    page = pdf.Page()
    doc.add_page(page)
    layout: pdf.PageLayout = pdf.SingleColumnLayout(page)
    bots = list(filter(lambda bot: bot.is_sellable(), DBot.objects.all()))

    layout.add(pdf.Paragraph(
        text="Delivery bots price list",
        horizontal_alignment=pdf.Alignment.CENTERED,
        font="times-roman",
    ))
    layout.add(pdf.Paragraph(
        text=f"Generated automatically on {date} at {time}",
        horizontal_alignment=pdf.Alignment.RIGHT,
        font="times-italic",
    ))
    table = pdf.FixedColumnWidthTable(
        number_of_rows=len(bots) + 1,
        number_of_columns=3,
    )

    table.add(pdf.Paragraph(
        text="Vendor code",
        horizontal_alignment=pdf.Alignment.CENTERED,
        font="times-roman",
    ))
    table.add(pdf.Paragraph(
        text="Name",
        horizontal_alignment=pdf.Alignment.CENTERED,
        font="times-roman",
    ))
    table.add(pdf.Paragraph(
        text="Price",
        horizontal_alignment=pdf.Alignment.CENTERED,
        font="times-roman",
    ))

    for bot in bots:
        table.add(pdf.Paragraph(
            text=bot.vendor_code,
            font="times-roman",
        ))
        table.add(pdf.Paragraph(
            text=bot.name,
            font="times-roman",
        ))
        table.add(pdf.Paragraph(
            text=str(bot.price),
            font="times-roman",
        ))

    layout.add(table)


    response = HttpResponse(
        doc,
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f'attachment; filename="price_list_{date}.pdf"'
        },

    )
    return response