from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditLog, Course, Selection, SiteSetting, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("选课系统", {"fields": ("role", "display_name", "department", "must_change_password")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("选课系统", {"fields": ("role", "display_name", "department")}),)
    list_display = ("username", "display_name", "department", "role", "is_active")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "capacity", "is_active")
    search_fields = ("code", "name")


admin.site.register(Selection)
admin.site.register(SiteSetting)
admin.site.register(AuditLog)
