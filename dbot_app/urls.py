from django.shortcuts import redirect
from django.urls import path

from . import views

urlpatterns = [
    path('auth/signup', views.signup, name='signup'),
    path('auth/signin', views.signin, name='signin'),
    path('auth/logout', views.log_out, name='logout'),
    path('auth/unauthorized', views.unauthorized, name='unauthorized'),
    path('auth/disabled', views.disabled_account, name='disabled_account'),
    path('auth/invalid_credentials', views.invalid_credentials, name='invalid_credentials'),

    path('manage/roles', views.manage_roles, name='manage_roles'),
    path('manage/accounts', views.manage_accounts, name='manage_accounts'),
    path('manage/parts', views.manage_parts, name='parts'),

    path('', lambda request: redirect('home')),
    path('home', views.home, name='home'),

    path('admin', views.admin_menu, name='admin_menu'),

    path('logs/auth', views.auth_logs, name='auth_logs'),

    path('processes/main', views.processes_main, name='processes_main'),
    path('processes/new', views.processes_new, name='processes_new'),
    path('processes/<str:pk>', views.process, name='process'),

    path('bots', views.bots, name='bots'),
    path('bots/generate_price_list', views.generate_price_list, name='generate_price_list'),

]