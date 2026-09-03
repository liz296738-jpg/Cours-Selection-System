from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def portal_admin_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_portal_admin:
            messages.error(request, "你没有管理员权限。")
            return redirect("teacher_courses")
        return view(request, *args, **kwargs)
    return wrapped


def teacher_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.role != request.user.Role.TEACHER:
            return redirect("control_dashboard")
        if request.user.must_change_password:
            return redirect("change_password")
        return view(request, *args, **kwargs)
    return wrapped
