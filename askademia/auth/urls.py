from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
#routes
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
]