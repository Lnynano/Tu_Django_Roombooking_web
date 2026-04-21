# bookings/admin.py

from django.contrib import admin
from .models import Room, Booking

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity', 'location', 'is_active')
    search_fields = ('name', 'location')
    list_filter = ('is_active',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'start_time', 'room')
    search_fields = ('user__tu_id', 'user__first_name', 'room__name')
    date_hierarchy = 'start_time'
