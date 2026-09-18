
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .forms import RegistrationForm
from .models import (
    User,
    ParkingLocation,
    ParkingSlot,
    Booking,
    Complaint
)


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

def home(request):
    return render(request, 'parking/home.html')


# ---------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------

def register(request):

    if request.method == 'POST':

        form = RegistrationForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            # Full name
            user.first_name = form.cleaned_data['full_name']

            # Email
            email = form.cleaned_data['email'].strip().lower()
            user.email = email

            # Generate username automatically
            username = email.split('@')[0]

            # Make sure username is unique
            original_username = username
            counter = 1

            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1

            user.username = username

            # Password
            user.set_password(
                form.cleaned_data['password']
            )

            # Role selected from registration page
            user.role = request.POST.get('role', 'user')

            user.save()

            messages.success(
                request,
                'Account created successfully! Please login.'
            )

            return redirect('login')

    else:

        form = RegistrationForm()

    return render(
        request,
        'parking/register.html',
        {'form': form}
    )


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

def user_login(request):

    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)

            authenticated_user = authenticate(
                request,
                username=user.username,
                password=password
            )

            if authenticated_user is not None:

                login(request, authenticated_user)

                if authenticated_user.role == 'user':
                    return redirect('user_dashboard')

                elif authenticated_user.role == 'manager':
                    return redirect('manager_dashboard')

                elif authenticated_user.role == 'admin':
                    return redirect('admin_dashboard')

            else:
                messages.error(
                    request,
                    'Invalid email or password.'
                )

        except User.DoesNotExist:

            messages.error(
                request,
                'Invalid email or password.'
            )

    return render(
        request,
        'parking/login.html'
    )


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

def user_logout(request):

    logout(request)

    return redirect('login')


# ---------------------------------------------------------
# USER DASHBOARD
# ---------------------------------------------------------

def user_dashboard(request):

    return render(
        request,
        'parking/user_dashboard.html'
    )


# ---------------------------------------------------------
# MANAGER DASHBOARD
# ---------------------------------------------------------

def manager_dashboard(request):

    return render(
        request,
        'parking/manager_dashboard.html'
    )


# ---------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------


def admin_dashboard(request):

    total_users = User.objects.filter(role='user').count()
    total_managers = User.objects.filter(role='manager').count()
    total_locations = ParkingLocation.objects.count()
    total_slots = ParkingSlot.objects.count()
    active_bookings = Booking.objects.filter(
        status__in=['reserved', 'active']
    ).count()
    total_complaints = Complaint.objects.count()

    context = {
        'total_users': total_users,
        'total_managers': total_managers,
        'total_locations': total_locations,
        'total_slots': total_slots,
        'active_bookings': active_bookings,
        'total_complaints': total_complaints,
    }

    return render(
        request,
        'parking/admin_dashboard.html',
        context
    )


