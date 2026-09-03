from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from selection.models import Course, SiteSetting, User


class Command(BaseCommand):
    help = "创建仅供本地预览的管理员、教师和示例课程"

    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(username="admin", defaults={
            "display_name": "系统管理员", "role": User.Role.ADMIN,
            "is_staff": True, "is_superuser": True, "must_change_password": False,
        })
        admin.set_password("Admin12345")
        admin.save()

        teacher, _ = User.objects.get_or_create(username="teacher01", defaults={
            "display_name": "张老师", "department": "招生就业处",
            "role": User.Role.TEACHER, "must_change_password": False,
        })
        teacher.set_password("Teacher12345")
        teacher.must_change_password = False
        teacher.save()

        samples = [
            ("KC001", "大学生职业生涯规划", "职业发展", 20, "帮助学生建立职业目标与行动计划。"),
            ("KC002", "就业指导实务", "就业指导", 15, "覆盖简历、面试与就业手续等实务内容。"),
            ("KC003", "创新创业基础", "创新创业", 10, "围绕项目设计、团队协作与商业表达开展教学。"),
            ("KC004", "大学生求职能力训练", "实践课程", 8, "通过模拟招聘提升求职沟通和面试能力。"),
        ]
        for code, name, category, capacity, description in samples:
            Course.objects.update_or_create(code=code, defaults={
                "name": name, "category": category, "capacity": capacity,
                "description": description, "is_active": True, "created_by": admin,
            })

        setting = SiteSetting.load()
        setting.selection_enabled = True
        setting.selection_start = timezone.now() - timedelta(days=1)
        setting.selection_end = timezone.now() + timedelta(days=30)
        setting.max_courses_per_teacher = 2
        setting.notice = "试用期间每位教师最多选择 2 门课程。"
        setting.save()
        self.stdout.write(self.style.SUCCESS("演示数据已创建：admin / Admin12345，teacher01 / Teacher12345"))
