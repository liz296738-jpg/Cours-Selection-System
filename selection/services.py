from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import AuditLog, Course, Selection, SiteSetting, User


@transaction.atomic
def select_course(*, teacher: User, course_id: int) -> Selection:
    teacher = User.objects.select_for_update().get(pk=teacher.pk)
    setting = SiteSetting.objects.select_for_update().get_or_create(pk=1)[0]
    course = Course.objects.select_for_update().get(pk=course_id)

    if teacher.role != User.Role.TEACHER or not teacher.is_active:
        raise ValidationError("当前账号不能选课。")
    if not setting.is_open:
        raise ValidationError("当前不在选课开放时间内。")
    if not course.is_active:
        raise ValidationError("该课程当前不可选。")
    if Selection.objects.filter(teacher=teacher).count() >= setting.max_courses_per_teacher:
        raise ValidationError(f"每位教师最多选择 {setting.max_courses_per_teacher} 门课程。")
    if Selection.objects.filter(course=course).count() >= course.capacity:
        raise ValidationError("该课程名额已满。")

    try:
        selection = Selection.objects.create(teacher=teacher, course=course)
    except IntegrityError as exc:
        raise ValidationError("你已经选择过这门课程。") from exc
    AuditLog.objects.create(user=teacher, action="选择课程", detail=str(course))
    return selection


@transaction.atomic
def cancel_selection(*, teacher: User, selection_id: int) -> None:
    setting = SiteSetting.objects.select_for_update().get_or_create(pk=1)[0]
    if not setting.is_open:
        raise ValidationError("当前不在选课开放时间内，不能取消。")
    selection = Selection.objects.select_for_update().select_related("course").filter(
        pk=selection_id, teacher=teacher
    ).first()
    if not selection:
        raise ValidationError("未找到这条选课记录。")
    course_text = str(selection.course)
    selection.delete()
    AuditLog.objects.create(user=teacher, action="取消课程", detail=course_text)
