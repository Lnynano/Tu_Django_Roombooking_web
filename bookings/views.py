# bookings/views.py

import calendar as cal_module
from datetime import timedelta, date

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Room, Booking, BlackoutPeriod
from .forms import BookingForm, RoomForm, BlackoutPeriodForm

@login_required
def room_list(request):
    """รายการห้องประชุมทั้งหมด"""
    rooms = Room.objects.filter(is_active=True)
    context = {'rooms': rooms}

    date_str = request.GET.get('date')
    if date_str:
        try:
            selected = date.fromisoformat(date_str)
            THAI_MONTHS_SHORT = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                                  'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
            context['selected_date'] = date_str
            context['selected_date_display'] = (
                f"{selected.day} {THAI_MONTHS_SHORT[selected.month]} {selected.year}"
            )
        except ValueError:
            pass

    return render(request, 'bookings/room_list.html', context)

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

                # Check blackout periods across every occurrence
                blackout_dates = []
                for occ_start, occ_end in occurrences:
                    occ_date = occ_start.date()
                    if BlackoutPeriod.objects.filter(
                        is_active=True,
                        start_date__lte=occ_date,
                        end_date__gte=occ_date,
                    ).exists():
                        blackout_dates.append(occ_start.strftime('%d/%m/%Y'))

                if blackout_dates:
                    messages.error(
                        request,
                        'พบวันที่อยู่ในช่วงปิดการจอง: ' + ', '.join(blackout_dates),
                    )
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
        initial = {}
        date_str = request.GET.get('date')
        if date_str:
            try:
                date.fromisoformat(date_str)
                initial['start_date'] = date_str
            except ValueError:
                pass
        form = BookingForm(room=room, initial=initial)

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
def calendar_view(request):
    """ปฏิทินการจองห้องประชุม (รายเดือน/รายสัปดาห์)"""
    THAI_MONTHS = ['', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
                   'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม']
    THAI_MONTHS_SHORT = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                         'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']
    THAI_DAYS_SHORT = ['จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส', 'อา']  # Mon=0..Sun=6

    today = timezone.now().date()
    view_type = request.GET.get('view', 'month')

    if view_type == 'week':
        week_start_str = request.GET.get('week_start')
        if week_start_str:
            try:
                week_start = date.fromisoformat(week_start_str)
            except ValueError:
                week_start = today - timedelta(days=today.weekday())
        else:
            week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        bookings = Booking.objects.filter(
            status__in=['Pending', 'Approved'],
            start_time__date__gte=week_start,
            start_time__date__lte=week_end,
        ).select_related('room', 'user').order_by('start_time')

        bookings_by_date = {}
        for b in bookings:
            d = b.start_time.date()
            bookings_by_date.setdefault(d, []).append(b)

        week_days = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            week_days.append({
                'date': d,
                'thai_day': THAI_DAYS_SHORT[d.weekday()],
                'thai_month': THAI_MONTHS_SHORT[d.month],
                'bookings': bookings_by_date.get(d, []),
                'is_today': d == today,
            })

        if week_start.month == week_end.month:
            week_title = f"{week_start.day} - {week_end.day} {THAI_MONTHS[week_start.month]} {week_end.year}"
        else:
            week_title = (f"{week_start.day} {THAI_MONTHS_SHORT[week_start.month]} "
                          f"- {week_end.day} {THAI_MONTHS_SHORT[week_end.month]} {week_end.year}")

        context = {
            'view_type': 'week',
            'week_days': week_days,
            'week_start': week_start,
            'week_end': week_end,
            'week_title': week_title,
            'prev_week': (week_start - timedelta(days=7)).isoformat(),
            'next_week': (week_start + timedelta(days=7)).isoformat(),
            'today': today,
            'THAI_MONTHS': THAI_MONTHS,
        }
    else:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))

        bookings = Booking.objects.filter(
            status__in=['Pending', 'Approved'],
            start_time__year=year,
            start_time__month=month,
        ).select_related('room', 'user').order_by('start_time')

        bookings_by_date = {}
        for b in bookings:
            d = b.start_time.date()
            bookings_by_date.setdefault(d, []).append(b)

        raw_weeks = cal_module.monthcalendar(year, month)
        weeks = []
        for week in raw_weeks:
            week_days = []
            for day in week:
                if day == 0:
                    week_days.append(None)
                else:
                    d = date(year, month, day)
                    week_days.append({
                        'date': d,
                        'day': day,
                        'bookings': bookings_by_date.get(d, []),
                        'is_today': d == today,
                    })
            weeks.append(week_days)

        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1

        this_week_start = (today - timedelta(days=today.weekday())).isoformat()

        context = {
            'view_type': 'month',
            'weeks': weeks,
            'year': year,
            'month': month,
            'month_name': THAI_MONTHS[month],
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'today': today,
            'this_week_start': this_week_start,
        }

    return render(request, 'bookings/calendar.html', context)


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


@admin_required
def manage_blackout(request):
    periods = BlackoutPeriod.objects.all()
    return render(request, 'bookings/manage_blackout.html', {'periods': periods})


@admin_required
def add_blackout(request):
    if request.method == 'POST':
        form = BlackoutPeriodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มช่วงปิดการจองเรียบร้อยแล้ว')
            return redirect('bookings:manage_blackout')
    else:
        form = BlackoutPeriodForm()
    return render(request, 'bookings/blackout_form.html', {'form': form, 'action': 'เพิ่มช่วงปิดการจอง'})


@admin_required
def edit_blackout(request, period_id):
    period = get_object_or_404(BlackoutPeriod, id=period_id)
    if request.method == 'POST':
        form = BlackoutPeriodForm(request.POST, instance=period)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขช่วงปิดการจองเรียบร้อยแล้ว')
            return redirect('bookings:manage_blackout')
    else:
        form = BlackoutPeriodForm(instance=period)
    return render(request, 'bookings/blackout_form.html', {'form': form, 'action': 'แก้ไขช่วงปิดการจอง', 'period': period})


@admin_required
def delete_blackout(request, period_id):
    period = get_object_or_404(BlackoutPeriod, id=period_id)
    if request.method == 'POST':
        period.delete()
        messages.success(request, 'ลบช่วงปิดการจองเรียบร้อยแล้ว')
    return redirect('bookings:manage_blackout')
