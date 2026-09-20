
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q


from .forms import RegistrationForm, ComplaintForm
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

            user.first_name = form.cleaned_data['full_name']

            email = form.cleaned_data['email'].strip().lower()
            user.email = email

            # Generate username automatically from email
            username = email.split('@')[0]
            original_username = username
            counter = 1

            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1

            user.username = username

            # Set password securely
            user.set_password(form.cleaned_data['password'])

            # Get selected role
            user.role = request.POST.get('role', 'user')

            # New accounts require admin approval
            user.approval_status = 'pending'
            user.is_active = False

            user.save()

            messages.success(
                request,
                'Registration successful! Your account is waiting for admin approval.'
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
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        try:
            user = User.objects.get(email=email)

            # Check whether the account is approved
            if user.approval_status == 'pending':
                messages.warning(
                    request,
                    'Your account is waiting for admin approval.'
                )
                return render(request, 'parking/login.html')

            if user.approval_status == 'rejected':
                messages.error(
                    request,
                    'Your account registration was rejected by the admin.'
                )
                return render(request, 'parking/login.html')

            # Check whether the account is active
            if not user.is_active:
                messages.error(
                    request,
                    'Your account is inactive. Please contact the admin.'
                )
                return render(request, 'parking/login.html')

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

    return render(request, 'parking/login.html')



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
        'parking/dashboard.html'
    )
# ---------------------------------------------------------
# PARKING LIST
# ---------------------------------------------------------

def parking_list(request):

    return render(
        request,
        'parking/parking_list.html'
    )

# ---------------------------------------------------------
# MANAGER DASHBOARD
# ---------------------------------------------------------


def admin_managers(request):
    managers = User.objects.filter(
        role='manager'
    ).order_by('-date_joined')

    search = request.GET.get('search', '').strip()

    if search:
        managers = managers.filter(
            Q(first_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(username__icontains=search)
        )

    context = {
        'managers': managers,
        'search': search,
    }

    return render(
        request,
        'parking/admin_managers.html',
        context
    )

def approve_manager(request, user_id):
    manager = User.objects.get(
        id=user_id,
        role='manager'
    )

    manager.approval_status = 'approved'
    manager.is_active = True
    manager.save()

    messages.success(
        request,
        f'{manager.first_name} has been approved as a Parking Manager.'
    )

    return redirect('admin_managers')


def reject_manager(request, user_id):
    manager = User.objects.get(
        id=user_id,
        role='manager'
    )

    manager.approval_status = 'rejected'
    manager.is_active = False
    manager.save()

    messages.warning(
        request,
        f'{manager.first_name} has been rejected.'
    )

    return redirect('admin_managers')



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


def admin_users(request):
    users = User.objects.filter(role='user').order_by('-date_joined')

    search = request.GET.get('search', '').strip()

    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(username__icontains=search)
        )

    context = {
        'users': users,
        'search': search,
    }

    return render(
        request,
        'parking/admin_users.html',
        context
    )

def approve_user(request, user_id):
    user = User.objects.get(
        id=user_id,
        role='user'
    )

    user.approval_status = 'approved'
    user.is_active = True
    user.save()

    messages.success(
        request,
        f'{user.first_name} has been approved successfully.'
    )

    return redirect('admin_users')


def reject_user(request, user_id):
    user = User.objects.get(
        id=user_id,
        role='user'
    )

    user.approval_status = 'rejected'
    user.is_active = False
    user.save()

    messages.warning(
        request,
        f'{user.first_name} has been rejected.'
    )

    return redirect('admin_users')

def deactivate_user(request, user_id):
    user = User.objects.get(
        id=user_id,
        role='user'
    )

    user.is_active = False
    user.save()

    messages.warning(
        request,
        f'{user.first_name} has been deactivated.'
    )

    return redirect('admin_users')

def activate_user(request, user_id):
    user = User.objects.get(
        id=user_id,
        role='user'
    )

    user.is_active = True
    user.approval_status = 'approved'
    user.save()

    messages.success(
        request,
        f'{user.first_name} has been activated.'
    )

    return redirect('admin_users')

# ---------------------------------------------------------
# MY BOOKINGS
# ---------------------------------------------------------

def my_bookings(request):
    return render(
        request,
        'parking/my_bookings.html'
    )

# ---------------------------------------------------------
# PARKING SLOTS
# ---------------------------------------------------------

def parking_slots(request):
    return render(
        request,
        'parking/parking_slots.html'
    )
# ---------------------------------------------------------
# BOOKING PAGE
# ---------------------------------------------------------

def booking(request):
    return render(
        request,
        'parking/booking.html'
    )
# ---------------------------------------------------------
# BOOKING CONFIRMATION
# ---------------------------------------------------------

def booking_confirmation(request):
    return render(
        request,
        'parking/booking_confirmation.html'
    )
    # ---------------------------------------------------------
# BOOKING DETAILS
# ---------------------------------------------------------

def booking_details(request):
    return render(
        request,
        'parking/booking_details.html'
    )
# ---------------------------------------------------------
# QR CODE
# ---------------------------------------------------------

def qr_code(request):
    return render(
        request,
        'parking/qr_code.html'
    )
    # ---------------------------------------------------------
# BOOKING HISTORY
# ---------------------------------------------------------

def booking_history(request):
    return render(
        request,
        'parking/booking_history.html'
    )
    # ---------------------------------------------------------
# COMPLAINTS
# ---------------------------------------------------------

def complaints(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)

        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()

            messages.success(
                request,
                'Complaint submitted successfully.'
            )

            return redirect('complaints')

    else:
        form = ComplaintForm()

    return render(
        request,
        'parking/complaints.html',
        {'form': form}
    )
    # ---------------------------------------------------------
# COMPLAINT STATUS
# ---------------------------------------------------------

def complaint_status(request):
    return render(
        request,
        'parking/complaint_status.html'
    )