# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from .forms import UserProfileForm
from .models import UserProfile

def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'authentication/home.html')

def login_view(request):
    """Login view with form and GitHub OAuth option"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'authentication/login.html', {'form': form})

@login_required
def dashboard(request):
    """Main dashboard after login"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect('complete_profile')
    
    return render(request, 'authentication/dashboard.html')

@login_required
def profile(request):
    """User profile view/edit"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect('complete_profile')
        
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'authentication/profile.html', {'form': form})

@login_required
def complete_profile(request):
    """Complete profile after first login"""
    try:
        profile = request.user.profile
        return redirect('profile')
    except UserProfile.DoesNotExist:
        if request.method == 'POST':
            form = UserProfileForm(request.POST)
            if form.is_valid():
                profile = form.save(commit=False)
                profile.user = request.user
                profile.save()
                return redirect('dashboard')
        else:
            form = UserProfileForm()
        
        return render(request, 'authentication/complete_profile.html', {'form': form})