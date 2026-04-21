# bookings/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Room, Booking
from .forms import BookingForm

@login_required
def room_list(request):
    """รายการห้องประชุมทั้งหมด"""
    rooms = Room.objects.filter(is_active=True)
    return render(request, 'bookings/room_list.html', {'rooms': rooms})

@login_required
def book_room(request, room_id):
    """หน้าจองห้องประชุม"""
    room = get_object_or_404(Room, id=room_id, is_active=True)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.room = room
            booking.save()
            messages.success(request, f'ส่งคำขอจองห้อง {room.name} เรียบร้อยแล้ว')
            return redirect('accounts:dashboard')
    else:
        form = BookingForm(initial={'room': room})
        
    return render(request, 'bookings/book_room.html', {
        'form': form,
        'room': room
    })

@login_required
def my_bookings(request):
    """รายการจองของผู้ใช้ปัจจุบัน"""
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})

from accounts.decorators import admin_required

@admin_required
def admin_approve_list(request):
    """หน้าสำหรับ Admin อนุมัติการจอง"""
    pending_bookings = Booking.objects.filter(status='Pending').order_by('created_at')
    return render(request, 'bookings/admin_approve_list.html', {'bookings': pending_bookings})

@admin_required
def approve_booking(request, booking_id, action):
    """Action สำหรับอนุมัติหรือปฏิเสธการจอง"""
    booking = get_object_or_404(Booking, id=booking_id)
    if action == 'approve':
        booking.status = 'Approved'
        messages.success(request, f'อนุมัติการจองห้อง {booking.room.name} แล้ว')
    elif action == 'reject':
        booking.status = 'Rejected'
        messages.warning(request, f'ปฏิเสธการจองห้อง {booking.room.name} แล้ว')
    
    booking.save()
    return redirect('bookings:admin_approve_list')
