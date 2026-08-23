from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect


def home(request):
    return render(request, "parking/home.html")


def register(request):

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        role = request.POST.get("role")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register")

        if User.objects.filter(username=email).exists():
            messages.error(
                request,
                "An account with this email already exists."
            )
            return redirect("register")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        name_parts = full_name.split(" ", 1)

        user.first_name = name_parts[0]

        if len(name_parts) > 1:
            user.last_name = name_parts[1]

        user.save()

        messages.success(
            request,
            "Account created successfully! Please login."
        )

        return redirect("login")

    return render(request, "parking/register.html")


def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            auth_login(request, user)

            messages.success(
                request,
                "Login successful! Welcome to ParkGrid."
            )

            return redirect("home")

        else:

            messages.error(
                request,
                "Invalid email or password."
            )

            return redirect("login")

    return render(request, "parking/login.html")