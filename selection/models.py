from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "管理员"
        TEACHER = "teacher", "教师"

    role = models.CharField("角色", max_length=10, choices=Role.choices, default=Role.TEACHER)
    display_name = models.CharField("姓名", max_length=50)
    department = models.CharField("部门", max_length=100, blank=True)
    must_change_password = models.BooleanField("首次登录需改密码", default=True)

    @property
    def is_portal_admin(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    def __str__(self):
        return self.display_name or self.username


class SiteSetting(models.Model):
    max_courses_per_teacher = models.PositiveSmallIntegerField(
        "每位教师最多选课数", default=1, validators=[MinValueValidator(1)]
    )
    selection_start = models.DateTimeField("选课开始时间", null=True, blank=True)
    selection_end = models.DateTimeField("选课截止时间", null=True, blank=True)
    selection_enabled = models.BooleanField("开放选课", default=False)
    notice = models.CharField("首页通知", max_length=300, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def is_open(self):
        now = timezone.now()
        if not self.selection_enabled:
            return False
        if self.selection_start and now < self.selection_start:
            return False
        if self.selection_end and now > self.selection_end:
            return False
        return True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "选课设置"


class Course(models.Model):
    code = models.CharField("课程编号", max_length=40, unique=True)
    name = models.CharField("课程名称", max_length=120)
    category = models.CharField("课程类别", max_length=60, blank=True)
    description = models.TextField("课程说明", blank=True)
    capacity = models.PositiveSmallIntegerField("名额", default=1, validators=[MinValueValidator(1)])
    is_active = models.BooleanField("可选", default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_courses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code", "id"]

    @property
    def selected_count(self):
        return self.selections.count()

    @property
    def remaining(self):
        return max(0, self.capacity - self.selected_count)

    def __str__(self):
        return f"{self.code} {self.name}"


class Selection(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="selections")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="selections")
    selected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["teacher", "course"], name="unique_teacher_course"),
        ]
        ordering = ["-selected_at"]

    def __str__(self):
        return f"{self.teacher} - {self.course}"


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=80)
    detail = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
