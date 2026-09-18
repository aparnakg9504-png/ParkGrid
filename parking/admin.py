from django.contrib import admin
from .models import (
    User,
    ParkingLocation,
    ParkingSlot,
    Booking,
    Payment,
    Complaint,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'phone',
        'role',
        'is_active',
    )

    list_filter = (
        'role',
        'is_active',
    )

    search_fields = (
        'username',
        'email',
        'phone',
    )


@admin.register(ParkingLocation)
class ParkingLocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'manager',
        'city',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'city',
    )

    search_fields = (
        'name',
        'city',
        'address',
    )


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = (
        'slot_number',
        'location',
        'vehicle_type',
        'is_ev',
        'charging_available',
        'status',
    )

    list_filter = (
        'vehicle_type',
        'is_ev',
        'status',
    )

    search_fields = (
        'slot_number',
        'location__name',
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'location',
        'slot',
        'vehicle_type',
        'vehicle_number',
        'booking_date',
        'status',
    )

    list_filter = (
        'status',
        'vehicle_type',
        'booking_date',
    )

    search_fields = (
        'vehicle_number',
        'user__username',
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'booking',
        'amount',
        'payment_method',
        'status',
        'payment_time',
    )

    list_filter = (
        'status',
        'payment_method',
    )


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'subject',
        'user',
        'location',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'subject',
        'description',
        'user__username',
    )