from django.urls import path

from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("daily-report/", views.daily_report, name="daily_report"),
    path("users/", views.user_list, name="users"),
    path("users/<int:pk>/toggle-active/", views.user_toggle_active, name="user_toggle_active"),
    path("users/<int:pk>/change-role/", views.user_change_role, name="user_change_role"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("exchanges/", views.exchange_list, name="exchanges"),
    path("reports/", views.report_list, name="reports"),
    path("reports/<int:pk>/update/", views.report_update, name="report_update"),
    path("skills/", views.skill_list, name="skills"),
    path("skills/<int:pk>/toggle-active/", views.skill_toggle_active, name="skill_toggle_active"),
    path("skills/<int:pk>/delete/", views.skill_delete, name="skill_delete"),
    path("categories/", views.category_list, name="categories"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
]
