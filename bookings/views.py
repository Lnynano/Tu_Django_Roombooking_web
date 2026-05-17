# bookings/views.py

from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Room, Booking
from .forms import BookingForm, RoomForm

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
        form = BookingForm(request.POST, room=room)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.room = room
            booking.start_time = form.cleaned_data['start_time']
            booking.end_time = form.cleaned_data['end_time']

            if booking.is_recurring:
                days_selected = [int(d) for d in form.cleaned_data['days_of_week']]
                booking.days_of_week = days_selected
                duration = booking.end_time - booking.start_time

                # Build list of matching occurrence dates
                occurrences = []
                current_date = booking.start_time.date()
                while current_date <= booking.recurring_end_date:
                    if current_date.weekday() in days_selected:
                        occ_start = booking.start_time.replace(
                            year=current_date.year,
                            month=current_date.month,
                            day=current_date.day,
                        )
                        occurrences.append((occ_start, occ_start + duration))
                    current_date += timedelta(days=1)

                if not occurrences:
                    messages.error(request, 'ไม่พบวันที่ตรงกับวันที่เลือกในช่วงเวลาที่กำหนด')
                    return render(request, 'bookings/book_room.html', {'form': form, 'room': room})

                # Check conflicts across every occurrence
                conflict_dates = []
                for occ_start, occ_end in occurrences:
                    conflict = Booking.objects.filter(
                        room=room,
                        status__in=['Pending', 'Approved'],
                        start_time__lt=occ_end,
                        end_time__gt=occ_start,
                    ).first()
                    if conflict:
                        conflict_dates.append(occ_start.strftime('%d/%m/%Y'))

                if conflict_dates:
                    messages.error(
                        request,
                        'พบการจองทับซ้อนในวันต่อไปนี้: ' + ', '.join(conflict_dates),
                    )
                    return render(request, 'bookings/book_room.html', {'form': form, 'room': room})

                # Save one Booking record per occurrence
                for occ_start, occ_end in occurrences:
                    Booking.objects.create(
                        user=request.user,
                        room=room,
                        objective_type=booking.objective_type,
                        start_time=occ_start,
                        end_time=occ_end,
                        purpose=booking.purpose,
                        is_recurring=True,
                        recurring_end_date=booking.recurring_end_date,
                        days_of_week=days_selected,
                        class_code=booking.class_code,
                        class_name=booking.class_name,
                        curriculum=booking.curriculum,
                        training_topic=booking.training_topic,
                    )
                messages.success(
                    request,
                    f'ส่งคำขอจองห้อง {room.name} แบบรายสัปดาห์ จำนวน {len(occurrences)} ครั้ง เรียบร้อยแล้ว',
                )
            else:
                booking.save()
                messages.success(request, f'ส่งคำขอจองห้อง {room.name} เรียบร้อยแล้ว')

            return redirect('accounts:dashboard')
    else:
        form = BookingForm(room=room)
        
    return render(request, 'bookings/book_room.html', {
        'form': form,
        'room': room
    })

@login_required
def my_bookings(request):
    """รายการจองของผู้ใช้ปัจจุบัน"""
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})

@login_required
def cancel_booking(request, booking_id):
    """ยกเลิกการจองโดยผู้ใช้"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == 'POST':
        if booking.status in ('Pending', 'Approved'):
            booking.status = 'Cancelled'
            booking.save()
            messages.success(request, f'ยกเลิกการจองห้อง {booking.room.name} เรียบร้อยแล้ว')
        else:
            messages.error(request, 'ไม่สามารถยกเลิกการจองนี้ได้')
    return redirect('bookings:my_bookings')

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
    booking.save()
    return redirect('bookings:admin_approve_list')

@admin_required
def manage_rooms(request):
    """หน้าจัดการห้องประชุม (Admin)"""
    rooms = Room.objects.all().order_by('-id')
    return render(request, 'bookings/manage_rooms.html', {'rooms': rooms})

@admin_required
def add_room(request):
    """หน้าเพิ่มห้องประชุมใหม่ (Admin)"""
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มห้องประชุมใหม่เรียบร้อยแล้ว')
            return redirect('bookings:manage_rooms')
    else:
        form = RoomForm()
    
    return render(request, 'bookings/room_form.html', {
        'form': form,
        'action': 'เพิ่มห้องประชุม'
    })

@admin_required
def edit_room(request, room_id):
    """หน้าแก้ไขห้องประชุม (Admin)"""
    room = get_object_or_404(Room, id=room_id)
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f'อัปเดตข้อมูลห้อง {room.name} เรียบร้อยแล้ว')
            return redirect('bookings:manage_rooms')
    else:
        form = RoomForm(instance=room)
    
    return render(request, 'bookings/room_form.html', {
        'form': form,
        'action': 'แก้ไขห้องประชุม',
        'room': room
    })

@admin_required
def delete_room(request, room_id):
    """ลบห้องประชุม (Admin)"""
    room = get_object_or_404(Room, id=room_id)
    # We could do soft delete: room.is_active = False
    # Or hard delete: room.delete()
    # Let's do hard delete for now or soft delete based on standard. I'll do hard delete, 
    # but maybe soft delete is safer if there are existing bookings.
    room.is_active = False
    room.save()
    messages.success(request, f'ระงับการใช้งานห้อง {room.name} เรียบร้อยแล้ว')
    return redirect('bookings:manage_rooms')
