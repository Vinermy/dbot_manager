# Generated by Django 5.0.3 on 2024-03-16 07:38

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='DBotPart',
            fields=[
                ('vendor_code', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('name', models.CharField(default='', max_length=512)),
                ('weight', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('manufacture_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='DBotPartKind',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=512)),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=150)),
                ('can_edit_parts', models.BooleanField(default=False)),
                ('can_edit_bots', models.BooleanField(default=False)),
                ('can_start_process', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('role', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profiles', to='dbot_app.role')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='DBot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(default='', max_length=512)),
                ('vendor_code', models.CharField(max_length=20, unique=True)),
                ('state', models.CharField(choices=[('DS', 'Проектируется'), ('MN', 'В серийном производстве'), ('DC', 'Снят с производства')], default='DS', max_length=2)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('parts', models.ManyToManyField(related_name='bots', to='dbot_app.dbotpart')),
            ],
        ),
        migrations.AddField(
            model_name='dbotpart',
            name='kind',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parts', to='dbot_app.dbotpartkind'),
        ),
        migrations.CreateModel(
            name='LaunchProcess',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_finished', models.BooleanField(default=False)),
                ('bot', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='launch_process', to='dbot_app.dbot')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('text', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now=True, null=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comments', to=settings.AUTH_USER_MODEL)),
                ('launch_process', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='dbot_app.launchprocess')),
            ],
        ),
        migrations.CreateModel(
            name='LaunchStage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=512)),
                ('requires_parts_access', models.BooleanField(default=False)),
                ('previous_stage', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='next_stage', to='dbot_app.launchstage')),
                ('responsible_role', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stages_responsible', to='dbot_app.role')),
            ],
        ),
        migrations.AddField(
            model_name='launchprocess',
            name='stage',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processes', to='dbot_app.launchstage'),
        ),
    ]
