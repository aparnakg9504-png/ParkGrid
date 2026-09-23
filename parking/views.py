from datetime import datetime, timedelta
import base64
from io import BytesIO
import uuid

import qrcode

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

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

            username = email.split('@')[0]
            original_username = username
            counter = 1

            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1

            user.username = username

            user.set_password(form.cleaned_data['password'])

            user.role = request.POST.get('role', 'user')

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

    locations = ParkingLocation.objects.filter(
        status=True
    ).order_by('name')

    for location in locations:
        location.available_slots = ParkingSlot.objects.filter(
            location=location,
            status='available'
        ).count()

    return render(
        request,
        'parking/parking_list.html',
        {
            'locations': locations,
        }
    )


# ---------------------------------------------------------
# PARKING LAYOUT
# ---------------------------------------------------------

def parking_layout(request, location_id):

    location = ParkingLocation.objects.get(
        id=location_id
    )

    slots = ParkingSlot.objects.filter(
        location=location
    ).order_by('slot_number')

    selected_date = request.GET.get('date')
    selected_time = request.GET.get('time')
    duration_value = request.GET.get('duration')

    booked_slot_ids = set()
    duration = None

    # Check which slots are already booked
    if selected_date and selected_time and duration_value:

        try:

            duration = int(duration_value)

            if duration > 0:

                start_naive = datetime.strptime(
                    f"{selected_date} {selected_time}",
                    "%Y-%m-%d %H:%M"
                )

                start_time = timezone.make_aware(
                    start_naive
                )

                end_time = start_time + timedelta(
                    hours=duration
                )

                conflicting_bookings = Booking.objects.filter(
                    location=location,
                    status__in=['reserved', 'active'],
                    expected_arrival__lt=end_time,
                    reservation_expiry__gt=start_time
                )

                booked_slot_ids = set(
                    conflicting_bookings.values_list(
                        'slot_id',
                        flat=True
                    )
                )

        except (ValueError, TypeError):

            duration = None

    return render(
        request,
        'parking/parking_layout.html',
        {
            'location': location,
            'slots': slots,
            'booked_slot_ids': booked_slot_ids,
            'selected_date': selected_date,
            'selected_time': selected_time,
            'duration': duration,
        }
    )


# ---------------------------------------------------------
# PARKING SLOT DETAILS
# ---------------------------------------------------------

def parking_slots(request):

    slot_id = request.GET.get('slot_id')

    slot = None

    if slot_id:

        try:
            slot = ParkingSlot.objects.get(
                id=slot_id
            )

        except ParkingSlot.DoesNotExist:
            slot = None

    return render(
        request,
        'parking/parking_slots.html',
        {
            'slot': slot
        }
    )


# =========================================================
# MANAGER SECTION
# =========================================================


# ---------------------------------------------------------
# MANAGER DASHBOARD
# ---------------------------------------------------------

def manager_dashboard(request):

    manager = request.user

    try:

        location = ParkingLocation.objects.get(
            manager=manager
        )

    except ParkingLocation.DoesNotExist:

        location = None

    if location:

        total_slots = ParkingSlot.objects.filter(
            location=location
        ).count()

        available_slots = ParkingSlot.objects.filter(
            location=location,
            status='available'
        ).count()

        occupied_slots = ParkingSlot.objects.filter(
            location=location,
            status='occupied'
        ).count()

        total_bookings = Booking.objects.filter(
            location=location
        ).count()

        active_bookings = Booking.objects.filter(
            location=location,
            status__in=['reserved', 'active']
        ).count()

        total_complaints = Complaint.objects.filter(
            location=location
        ).count()

    else:

        total_slots = 0
        available_slots = 0
        occupied_slots = 0
        total_bookings = 0
        active_bookings = 0
        total_complaints = 0

    context = {
        'location': location,
        'total_slots': total_slots,
        'available_slots': available_slots,
        'occupied_slots': occupied_slots,
        'total_bookings': total_bookings,
        'active_bookings': active_bookings,
        'total_complaints': total_complaints,
    }

    return render(
        request,
        'parking/manager_dashboard.html',
        context
    )


# ---------------------------------------------------------
# MANAGER PARKING FACILITY
# ---------------------------------------------------------

def manager_facility(request):

    location = ParkingLocation.objects.filter(
        manager=request.user
    ).first()

    if request.method == 'POST':

        if location:

            messages.error(
                request,
                'You already have a parking facility.'
            )

            return redirect('manager_facility')

        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')

        ParkingLocation.objects.create(
            manager=request.user,
            name=name,
            address=address,
            city=city
        )

        messages.success(
            request,
            'Parking facility added successfully!'
        )

        return redirect('manager_facility')

    return render(
        request,
        'parking/manager_facility.html',
        {
            'location': location,
        }
    )


# ---------------------------------------------------------
# MANAGE PARKING SLOTS
# ---------------------------------------------------------

def manager_slots(request):

    location = ParkingLocation.objects.filter(
        manager=request.user
    ).first()

    if not location:

        messages.error(
            request,
            'Please add your parking facility first.'
        )

        return redirect('manager_facility')

    slots = ParkingSlot.objects.filter(
        location=location
    ).order_by('slot_number')

    if request.method == 'POST':

        slot_number = request.POST.get('slot_number')
        vehicle_type = request.POST.get('vehicle_type')
        is_ev = request.POST.get('is_ev') == 'on'
        charging_available = request.POST.get(
            'charging_available'
        ) == 'on'

        ParkingSlot.objects.create(
            location=location,
            slot_number=slot_number,
            vehicle_type=vehicle_type,
            is_ev=is_ev,
            charging_available=charging_available
        )

        messages.success(
            request,
            f'Slot {slot_number} added successfully!'
        )

        return redirect('manager_slots')

    return render(
        request,
        'parking/manager_slots.html',
        {
            'location': location,
            'slots': slots,
        }
    )


# ---------------------------------------------------------
# EDIT PARKING SLOT
# ---------------------------------------------------------

def edit_manager_slot(request, slot_id):

    slot = ParkingSlot.objects.get(
        id=slot_id,
        location__manager=request.user
    )

    if request.method == 'POST':

        slot.slot_number = request.POST.get(
            'slot_number'
        )

        slot.vehicle_type = request.POST.get(
            'vehicle_type'
        )

        slot.is_ev = request.POST.get(
            'is_ev'
        ) == 'on'

        slot.charging_available = request.POST.get(
            'charging_available'
        ) == 'on'

        slot.status = request.POST.get(
            'status'
        )

        slot.save()

        messages.success(
            request,
            f'Slot {slot.slot_number} updated successfully!'
        )

        return redirect('manager_slots')

    return render(
        request,
        'parking/edit_manager_slot.html',
        {
            'slot': slot,
        }
    )


# ---------------------------------------------------------
# DELETE PARKING SLOT
# ---------------------------------------------------------

def delete_manager_slot(request, slot_id):

    slot = ParkingSlot.objects.get(
        id=slot_id,
        location__manager=request.user
    )

    if request.method == 'POST':

        slot_number = slot.slot_number

        slot.delete()

        messages.success(
            request,
            f'Slot {slot_number} deleted successfully!'
        )

    return redirect('manager_slots')


# ---------------------------------------------------------
# MANAGER BOOKINGS
# ---------------------------------------------------------

def manager_bookings(request):

    location = ParkingLocation.objects.filter(
        manager=request.user
    ).first()

    if not location:

        messages.error(
            request,
            'Please add your parking facility first.'
        )

        return redirect('manager_facility')

    bookings = Booking.objects.filter(
        location=location
    ).select_related(
        'user',
        'slot'
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'parking/manager_bookings.html',
        {
            'location': location,
            'bookings': bookings,
        }
    )


# ---------------------------------------------------------
# MANAGER COMPLAINTS
# ---------------------------------------------------------

def manager_complaints(request):

    location = ParkingLocation.objects.filter(
        manager=request.user
    ).first()

    if not location:

        messages.error(
            request,
            'Please add your parking facility first.'
        )

        return redirect('manager_facility')

    complaints = Complaint.objects.filter(
        location=location
    ).select_related(
        'user',
        'booking'
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'parking/manager_complaints.html',
        {
            'location': location,
            'complaints': complaints,
        }
    )


# =========================================================
# ADMIN SECTION
# =========================================================


# ---------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------

def admin_dashboard(request):

    total_users = User.objects.filter(
        role='user'
    ).count()

    total_managers = User.objects.filter(
        role='manager'
    ).count()

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


# ---------------------------------------------------------
# ADMIN USERS
# ---------------------------------------------------------

def admin_users(request):

    users = User.objects.filter(
        role='user'
    ).order_by('-date_joined')

    search = request.GET.get(
        'search',
        ''
    ).strip()

    if search:

        users = users.filter(
            Q(first_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(username__icontains=search)
        )

    return render(
        request,
        'parking/admin_users.html',
        {
            'users': users,
            'search': search,
        }
    )


# ---------------------------------------------------------
# APPROVE USER
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# REJECT USER
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# DEACTIVATE USER
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# ACTIVATE USER
# ---------------------------------------------------------

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
# ADMIN MANAGERS
# ---------------------------------------------------------

def admin_managers(request):

    managers = User.objects.filter(
        role='manager'
    ).order_by('-date_joined')

    search = request.GET.get(
        'search',
        ''
    ).strip()

    if search:

        managers = managers.filter(
            Q(first_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(username__icontains=search)
        )

    return render(
        request,
        'parking/admin_managers.html',
        {
            'managers': managers,
            'search': search,
        }
    )


# ---------------------------------------------------------
# APPROVE MANAGER
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# REJECT MANAGER
# ---------------------------------------------------------

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
# ADMIN PARKING LOCATIONS
# ---------------------------------------------------------

def admin_parking_locations(request):

    locations = ParkingLocation.objects.select_related(
        'manager'
    ).order_by('-created_at')

    search = request.GET.get(
        'search',
        ''
    ).strip()

    if search:

        locations = locations.filter(
            Q(name__icontains=search) |
            Q(city__icontains=search) |
            Q(address__icontains=search) |
            Q(manager__first_name__icontains=search) |
            Q(manager__email__icontains=search)
        )

    return render(
        request,
        'parking/admin_parking_locations.html',
        {
            'locations': locations,
            'search': search,
        }
    )


# ---------------------------------------------------------
# ADMIN BOOKINGS
# ---------------------------------------------------------

def admin_bookings(request):

    bookings = Booking.objects.select_related(
        'user',
        'location',
        'slot'
    ).order_by(
        '-created_at'
    )

    search = request.GET.get(
        'search',
        ''
    ).strip()

    if search:

        bookings = bookings.filter(
            Q(vehicle_number__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(location__name__icontains=search) |
            Q(slot__slot_number__icontains=search)
        )

    return render(
        request,
        'parking/admin_bookings.html',
        {
            'bookings': bookings,
            'search': search,
        }
    )


# ---------------------------------------------------------
# ADMIN COMPLAINTS
# ---------------------------------------------------------

def admin_complaints(request):

    complaints = Complaint.objects.select_related(
        'user',
        'location',
        'booking'
    ).order_by(
        '-created_at'
    )

    search = request.GET.get(
        'search',
        ''
    ).strip()

    if search:

        complaints = complaints.filter(
            Q(subject__icontains=search) |
            Q(description__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(location__name__icontains=search)
        )

    return render(
        request,
        'parking/admin_complaints.html',
        {
            'complaints': complaints,
            'search': search,
        }
    )


# ---------------------------------------------------------
# ADMIN REPORTS
# ---------------------------------------------------------

def admin_reports(request):

    total_users = User.objects.filter(
        role='user'
    ).count()

    total_managers = User.objects.filter(
        role='manager'
    ).count()

    total_locations = ParkingLocation.objects.count()

    total_slots = ParkingSlot.objects.count()

    total_bookings = Booking.objects.count()

    completed_bookings = Booking.objects.filter(
        status='completed'
    ).count()

    cancelled_bookings = Booking.objects.filter(
        status='cancelled'
    ).count()

    expired_bookings = Booking.objects.filter(
        status='expired'
    ).count()

    total_complaints = Complaint.objects.count()

    resolved_complaints = Complaint.objects.filter(
        status='resolved'
    ).count()

    pending_complaints = Complaint.objects.filter(
        status='pending'
    ).count()

    context = {
        'total_users': total_users,
        'total_managers': total_managers,
        'total_locations': total_locations,
        'total_slots': total_slots,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'expired_bookings': expired_bookings,
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
        'pending_complaints': pending_complaints,
    }

    return render(
        request,
        'parking/admin_reports.html',
        context
    )


# =========================================================
# BOOKING SECTION
# =========================================================


# ---------------------------------------------------------
# BOOKING
# ---------------------------------------------------------

def booking(request):

    if request.method == 'POST':

        slot_id = request.POST.get('slot_id')
        selected_date = request.POST.get('date')
        selected_time = request.POST.get('time')
        duration_value = request.POST.get('duration')
        vehicle_type = request.POST.get('vehicle_type')
        vehicle_number = request.POST.get('vehicle_number')

    else:

        slot_id = request.GET.get('slot_id')
        selected_date = request.GET.get('date')
        selected_time = request.GET.get('time')
        duration_value = request.GET.get('duration')
        vehicle_type = request.GET.get('vehicle_type')
        vehicle_number = request.GET.get('vehicle_number')

    try:
        slot = ParkingSlot.objects.get(id=slot_id)
    except (ParkingSlot.DoesNotExist, TypeError, ValueError):
        messages.error(request, 'Selected parking slot was not found.')
        return redirect('parking_list')

    try:
        duration = int(duration_value)
    except (ValueError, TypeError):
        duration = None

    if not selected_date or not selected_time or not duration:
        messages.error(request, 'Please select date, time and duration.')
        return redirect(
            'parking_layout',
            location_id=slot.location.id
        )

    try:
        start_naive = datetime.strptime(
            f"{selected_date} {selected_time}",
            "%Y-%m-%d %H:%M"
        )

        expected_arrival = timezone.make_aware(start_naive)

        reservation_expiry = (
            expected_arrival + timedelta(hours=duration)
        )

    except (ValueError, TypeError):

        messages.error(
            request,
            'Invalid booking date or time.'
        )

        return redirect(
            'parking_layout',
            location_id=slot.location.id
        )

    conflicting_booking = Booking.objects.filter(
        slot=slot,
        status__in=['reserved', 'active'],
        expected_arrival__lt=reservation_expiry,
        reservation_expiry__gt=expected_arrival
    ).exists()

    if conflicting_booking:

        messages.error(
            request,
            'Sorry, this slot has already been booked for the selected time.'
        )

        return redirect(
            'parking_layout',
            location_id=slot.location.id
        )

    # CREATE BOOKING
    if request.method == 'POST':

        if not vehicle_type or not vehicle_number:

            messages.error(
                request,
                'Please enter all vehicle details.'
            )

            return redirect(
                'parking_layout',
                location_id=slot.location.id
            )

        booking_obj = Booking.objects.create(

            user=request.user,

            location=slot.location,

            slot=slot,

            vehicle_type=vehicle_type,

            vehicle_number=vehicle_number,

            booking_date=expected_arrival.date(),

            expected_arrival=expected_arrival,

            reservation_expiry=reservation_expiry,

            qr_code=str(uuid.uuid4()),

            status='reserved'
        )

        return redirect(
            'booking_confirmation',
            booking_id=booking_obj.id
        )

    return render(
        request,
        'parking/booking.html',
        {
            'slot': slot,
            'selected_date': selected_date,
            'selected_time': selected_time,
            'duration': duration,
            'vehicle_type': vehicle_type,
            'vehicle_number': vehicle_number,
            'expected_arrival': expected_arrival,
            'reservation_expiry': reservation_expiry,
        }
    )

# ---------------------------------------------------------
# BOOKING CONFIRMATION
# ---------------------------------------------------------

def booking_confirmation(request, booking_id):

    try:
        booking = Booking.objects.get(
            id=booking_id,
            user=request.user
        )
    except Booking.DoesNotExist:
        messages.error(request, 'Booking not found.')
        return redirect('booking_history')

    return render(
        request,
        'parking/booking_confirmation.html',
        {
            'booking': booking
        }
    )

# ---------------------------------------------------------
# BOOKING DETAILS
# ---------------------------------------------------------

def booking_details(request):

    try:
        booking = Booking.objects.filter(
            user=request.user
        ).select_related(
            'location',
            'slot'
        ).latest('created_at')

    except Booking.DoesNotExist:

        messages.error(
            request,
            'No booking found.'
        )

        return redirect('booking_history')

    return render(
        request,
        'parking/booking_details.html',
        {
            'booking': booking
        }
    )

# ---------------------------------------------------------
# QR CODE
# ---------------------------------------------------------

def qr_code(request, booking_id):

    try:
        booking = Booking.objects.get(
            id=booking_id,
            user=request.user
        )

    except Booking.DoesNotExist:

        messages.error(
            request,
            'Booking not found.'
        )

        return redirect('booking_history')

    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=4
    )

    qr.add_data(booking.qr_code)

    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color='black',
        back_color='white'
    )

    buffer = BytesIO()

    qr_image.save(
        buffer,
        format='PNG'
    )

    qr_image_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode('utf-8')

    return render(
        request,
        'parking/qr_code.html',
        {
            'booking': booking,
            'qr_image': qr_image_base64
        }
    )
# ---------------------------------------------------------
# BOOKING HISTORY
# ---------------------------------------------------------

def booking_history(request):

    bookings = Booking.objects.filter(
        user=request.user
    ).select_related(
        'location',
        'slot'
    ).order_by('-created_at')

    return render(
        request,
        'parking/booking_history.html',
        {
            'bookings': bookings
        }
    )

# =========================================================
# COMPLAINT SECTION
# =========================================================


# ---------------------------------------------------------
# COMPLAINTS
# ---------------------------------------------------------

def complaint(request):

    if request.method == 'POST':

        form = ComplaintForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            complaint = form.save(
                commit=False
            )

            complaint.user = request.user

            complaint.save()

            messages.success(
                request,
                'Complaint submitted successfully.'
            )

            return redirect('complaint')

    else:

        form = ComplaintForm()

    return render(
        request,
        'parking/complaints.html',
        {
            'form': form
        }
    )


# ---------------------------------------------------------
# COMPLAINT STATUS
# ---------------------------------------------------------

def complaint_status(request):

    complaints = Complaint.objects.filter(
        user=request.user
    ).select_related(
        'location'
    ).order_by('-created_at')

    return render(
        request,
        'parking/complaint_status.html',
        {
            'complaints': complaints
        }
    )