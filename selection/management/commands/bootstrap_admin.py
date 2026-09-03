import os

from django.core.management.base import BaseCommand

from selection.models import User


class Command(BaseCommand):
    help = "根据环境变量创建首个管理员（已存在则跳过）"

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME", "").strip()
        password = os.getenv("ADMIN_PASSWORD", "")
        name = os.getenv("ADMIN_NAME", "系统管理员").strip()
        if not username or not password:
            self.stdout.write("未配置 ADMIN_USERNAME/ADMIN_PASSWORD，跳过管理员初始化")
            return
        user, created = User.objects.get_or_create(username=username, defaults={
            "display_name": name, "role": User.Role.ADMIN, "is_staff": True,
            "is_superuser": True, "must_change_password": False,
        })
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"已创建管理员 {username}"))
        else:
            self.stdout.write(f"管理员 {username} 已存在，未修改密码")
