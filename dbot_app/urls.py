from django.urls import path

from . import views

urlpatterns = [
    path('auth/signup', views.signup, name='signup'),
    path('auth/signin', views.signin, name='signin'),
    path('auth/logout', views.log_out, name='logout'),

    path('manage/roles', views.manage_roles, name='manage_roles'),
    path('manage/accounts', views.manage_accounts, name='manage_accounts'),

    path('home', views.home, name='home')
]