from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .forms import UserLoginForm, UserRegisterForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to PowerPulse, {user.username}! Your account has been created.")
            return redirect("core:dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect(request.GET.get("next") or "core:dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("core:landing")


def demo_login_view(request):
    """Instant one-click demo login so evaluators can test immediately."""
    user, created = User.objects.get_or_create(username="admin", defaults={"email": "admin@powerpulse.local", "is_staff": True, "is_superuser": True})
    if created:
        user.set_password("admin123")
        user.save()
    login(request, user)
    messages.success(request, f"Logged in as Demo User ({user.username}). Ready to explore!")
    return redirect("core:dashboard")
