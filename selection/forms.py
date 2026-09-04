from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from .models import Course, SiteSetting, User


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.setdefault("class", "form-control")


class SiteSettingForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = ["max_courses_per_teacher", "selection_start", "selection_end", "selection_enabled", "notice"]
        widgets = {
            "selection_start": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "selection_end": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "notice": forms.Textarea(attrs={"rows": 4, "placeholder": "例如：请各位老师在周五前完成选课"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["selection_start"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["selection_end"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["notice"].label = "教师端公告"

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("selection_start"), cleaned.get("selection_end")
        if start and end and start >= end:
            raise forms.ValidationError("截止时间必须晚于开始时间。")
        return cleaned


class CourseForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = ["code", "name", "category", "description", "capacity", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_capacity(self):
        capacity = self.cleaned_data["capacity"]
        if self.instance.pk and self.instance.selections.count() > capacity:
            raise forms.ValidationError("名额不能低于当前已选教师人数。")
        return capacity


class TeacherForm(StyledFormMixin, forms.ModelForm):
    password = forms.CharField(label="重置密码", widget=forms.PasswordInput, required=False,
                               help_text="留空则不修改密码。")

    class Meta:
        model = User
        fields = ["username", "display_name", "department", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["password"].label = "初始密码"
            self.fields["password"].help_text = "新建教师时必填。"

    def clean_password(self):
        value = self.cleaned_data.get("password")
        if not self.instance.pk and not value:
            raise forms.ValidationError("新建教师时必须设置初始密码。")
        if value and len(value) < 8:
            raise forms.ValidationError("密码至少需要 8 位。")
        return value

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.TEACHER
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
            user.must_change_password = True
        if commit:
            user.save()
        return user


class ExcelUploadForm(StyledFormMixin, forms.Form):
    file = forms.FileField(label="Excel 文件", help_text="仅支持 .xlsx 文件")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("请上传 .xlsx 文件。")
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("文件不能超过 5 MB。")
        return f


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    pass
