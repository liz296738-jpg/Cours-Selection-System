from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("password/", views.change_password, name="change_password"),
    path("health/", views.health, name="health"),
    path("control/", views.control_dashboard, name="control_dashboard"),
    path("control/settings/", views.settings_edit, name="settings_edit"),
    path("control/courses/", views.course_list, name="course_list"),
    path("control/courses/new/", views.course_edit, name="course_create"),
    path("control/courses/<int:pk>/edit/", views.course_edit, name="course_edit"),
    path("control/courses/<int:pk>/toggle/", views.course_toggle, name="course_toggle"),
    path("control/courses/import/", views.import_courses, name="import_courses"),
    path("control/teachers/", views.teacher_list, name="teacher_list"),
    path("control/teachers/new/", views.teacher_edit, name="teacher_create"),
    path("control/teachers/<int:pk>/edit/", views.teacher_edit, name="teacher_edit"),
    path("control/teachers/import/", views.import_teachers, name="import_teachers"),
    path("control/template/<str:kind>/", views.download_template, name="download_template"),
    path("control/results/", views.results, name="results"),
    path("control/results/export/", views.export_results, name="export_results"),
    path("control/results/export-unselected/", views.export_unselected_teachers, name="export_unselected_teachers"),
    path("courses/", views.teacher_courses, name="teacher_courses"),
    path("courses/<int:pk>/choose/", views.choose_course, name="choose_course"),
    path("my-selections/", views.my_selections, name="my_selections"),
    path("my-selections/<int:pk>/cancel/", views.cancel_course, name="cancel_course"),
]
