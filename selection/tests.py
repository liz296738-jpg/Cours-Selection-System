from datetime import timedelta
from io import BytesIO

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook

from .models import AuditLog, Course, Selection, SiteSetting, User
from .services import cancel_selection, select_course


class BaseCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="AdminPass123", display_name="管理员",
            role=User.Role.ADMIN, must_change_password=False,
        )
        self.teacher = User.objects.create_user(
            username="teacher01", password="TeacherPass123", display_name="张老师",
            role=User.Role.TEACHER, must_change_password=False,
        )
        self.setting = SiteSetting.load()
        self.setting.selection_enabled = True
        self.setting.selection_start = timezone.now() - timedelta(hours=1)
        self.setting.selection_end = timezone.now() + timedelta(hours=1)
        self.setting.max_courses_per_teacher = 1
        self.setting.save()
        self.course = Course.objects.create(
            code="KC001", name="就业指导", capacity=1, created_by=self.admin,
        )


class SelectionServiceTests(BaseCase):
    def test_teacher_can_select_course(self):
        selected = select_course(teacher=self.teacher, course_id=self.course.pk)
        self.assertEqual(selected.teacher, self.teacher)
        self.assertTrue(AuditLog.objects.filter(action="选择课程").exists())

    def test_global_limit_is_enforced(self):
        other = Course.objects.create(code="KC002", name="职业规划", capacity=5, created_by=self.admin)
        select_course(teacher=self.teacher, course_id=self.course.pk)
        with self.assertRaisesMessage(ValidationError, "最多选择 1 门"):
            select_course(teacher=self.teacher, course_id=other.pk)

    def test_course_capacity_is_enforced(self):
        other_teacher = User.objects.create_user(
            username="teacher02", password="TeacherPass123", display_name="李老师",
            role=User.Role.TEACHER, must_change_password=False,
        )
        select_course(teacher=self.teacher, course_id=self.course.pk)
        with self.assertRaisesMessage(ValidationError, "名额已满"):
            select_course(teacher=other_teacher, course_id=self.course.pk)

    def test_closed_period_blocks_cancel(self):
        selection = select_course(teacher=self.teacher, course_id=self.course.pk)
        self.setting.selection_enabled = False
        self.setting.save()
        with self.assertRaisesMessage(ValidationError, "不在选课开放时间"):
            cancel_selection(teacher=self.teacher, selection_id=selection.pk)

    def test_cancel_removes_own_selection(self):
        selection = select_course(teacher=self.teacher, course_id=self.course.pk)
        cancel_selection(teacher=self.teacher, selection_id=selection.pk)
        self.assertFalse(Selection.objects.filter(pk=selection.pk).exists())


class PermissionTests(BaseCase):
    def test_teacher_cannot_open_control_panel(self):
        self.client.login(username="teacher01", password="TeacherPass123")
        response = self.client.get(reverse("control_dashboard"))
        self.assertRedirects(response, reverse("teacher_courses"))

    def test_admin_is_redirected_to_control_panel(self):
        self.client.login(username="admin", password="AdminPass123")
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("control_dashboard"))

    def test_first_login_requires_password_change(self):
        self.teacher.must_change_password = True
        self.teacher.save()
        self.client.login(username="teacher01", password="TeacherPass123")
        response = self.client.get(reverse("teacher_courses"))
        self.assertRedirects(response, reverse("change_password"))

    def test_choose_endpoint_rejects_get(self):
        self.client.login(username="teacher01", password="TeacherPass123")
        response = self.client.get(reverse("choose_course", args=[self.course.pk]))
        self.assertEqual(response.status_code, 405)

    def test_admin_pages_render(self):
        self.client.login(username="admin", password="AdminPass123")
        urls = [
            reverse("control_dashboard"), reverse("settings_edit"), reverse("course_list"),
            reverse("course_create"), reverse("course_edit", args=[self.course.pk]),
            reverse("teacher_list"), reverse("teacher_create"),
            reverse("teacher_edit", args=[self.teacher.pk]), reverse("import_courses"),
            reverse("import_teachers"), reverse("results"),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_teacher_pages_render(self):
        self.client.login(username="teacher01", password="TeacherPass123")
        for url in [reverse("teacher_courses"), reverse("my_selections"), reverse("change_password")]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class SettingsTests(BaseCase):
    def test_admin_can_change_max_courses(self):
        self.client.login(username="admin", password="AdminPass123")
        response = self.client.post(reverse("settings_edit"), {
            "max_courses_per_teacher": 3,
            "selection_enabled": "on",
            "notice": "测试通知",
        })
        self.assertRedirects(response, reverse("settings_edit"))
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.max_courses_per_teacher, 3)


class ImportTests(BaseCase):
    def _upload(self, url, headers, row):
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        ws.append(row)
        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)
        stream.name = "import.xlsx"
        self.client.login(username="admin", password="AdminPass123")
        return self.client.post(url, {"file": stream, "action": "preview"})

    def test_course_excel_import(self):
        response = self._upload(
            reverse("import_courses"),
            ["课程编号", "课程名称", "课程类别", "名额", "课程说明"],
            ["KC100", "测试课程", "通识", 6, "说明"],
        )
        self.assertContains(response, "确认导入")
        response = self.client.post(reverse("import_courses"), {"action": "confirm"})
        self.assertRedirects(response, reverse("course_list"))
        self.assertTrue(Course.objects.filter(code="KC100", capacity=6).exists())

    def test_teacher_excel_import(self):
        response = self._upload(
            reverse("import_teachers"),
            ["登录账号", "姓名", "部门", "初始密码"],
            ["teacher99", "王老师", "就业科", "TeacherPass999"],
        )
        self.assertContains(response, "确认导入")
        response = self.client.post(reverse("import_teachers"), {"action": "confirm"})
        self.assertRedirects(response, reverse("teacher_list"))
        user = User.objects.get(username="teacher99")
        self.assertTrue(user.check_password("TeacherPass999"))
        self.assertTrue(user.must_change_password)

    def test_course_import_rejects_capacity_below_existing_selection(self):
        self.course.capacity = 2
        self.course.save()
        other = User.objects.create_user(username="teacher02", password="TeacherPass123", display_name="李老师", role=User.Role.TEACHER)
        select_course(teacher=self.teacher, course_id=self.course.pk)
        select_course(teacher=other, course_id=self.course.pk)
        response = self._upload(
            reverse("import_courses"),
            ["课程编号", "课程名称", "课程类别", "名额", "课程说明"],
            ["KC001", "就业指导", "通识", 1, "说明"],
        )
        self.assertContains(response, "名额不能低于当前已选教师人数")

    def test_import_requires_confirmation_before_writing(self):
        response = self._upload(
            reverse("import_courses"),
            ["课程编号", "课程名称", "课程类别", "名额", "课程说明"],
            ["KC101", "预览课程", "通识", 6, "说明"],
        )
        self.assertContains(response, "确认导入")
        self.assertFalse(Course.objects.filter(code="KC101").exists())


class PublicTests(TestCase):
    def test_health(self):
        response = Client().get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_login_page_has_accessible_controls(self):
        response = Client().get(reverse("login"))
        self.assertContains(response, "西南科技大学 · 招生就业处")
        self.assertContains(response, 'autocomplete="username"')
        self.assertContains(response, 'autocomplete="current-password"')
        self.assertContains(response, "data-password-toggle")

    def test_login_failure_shows_inline_error(self):
        response = Client().post(reverse("login"), {"username": "missing", "password": "incorrect"})
        self.assertContains(response, "账号或密码错误，请重新输入。")
