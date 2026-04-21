from django.shortcuts import redirect
from functools import wraps


def admin_required(view_func):
    """อนุญาตเฉพาะ Admin เท่านั้น"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role != 'Admin':
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return view_func(request, *args, **kwargs)
    return wrapper


def lecturer_required(view_func):
    """อนุญาตเฉพาะ Lecturer และ Admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role not in ['Lecturer', 'Admin']:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return view_func(request, *args, **kwargs)
    return wrapper
