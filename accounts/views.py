from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def login_view(request):
    """หน้า Login — ยืนยันตัวตนผ่าน TU REST API"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        tu_id = request.POST.get('tu_id', '').strip()
        password = request.POST.get('password', '')

        if not tu_id or not password:
            messages.error(request, 'กรุณากรอก Username และ Password')
            return render(request, 'accounts/login.html')

        user = authenticate(request, tu_id=tu_id, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'ยินดีต้อนรับ {user.first_name} {user.last_name}')
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Username หรือ Password ไม่ถูกต้อง')

    return render(request, 'accounts/login.html')


def logout_view(request):
    """Logout — ล้าง session แล้ว redirect ไปหน้า login"""
    logout(request)
    messages.info(request, 'ออกจากระบบเรียบร้อยแล้ว')
    return redirect('accounts:login')


@login_required
def dashboard_view(request):
    """Dashboard — หน้าหลักหลัง login"""
    from bookings.models import Booking, Room
    
    my_bookings = Booking.objects.filter(user=request.user)
    
    context = {
        'user': request.user,
        'my_bookings_count': my_bookings.count(),
        'pending_count': my_bookings.filter(status='Pending').count(),
        'approved_count': my_bookings.filter(status='Approved').count(),
        'rooms_count': Room.objects.filter(is_active=True).count(),
    }
    return render(request, 'accounts/dashboard.html', context)
