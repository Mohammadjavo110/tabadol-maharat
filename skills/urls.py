from django.urls import path

from skills import views

app_name = "skills"

urlpatterns = [
    path("", views.skill_list, name="list"),
    path("new/", views.skill_create, name="create"),
    path("mine/", views.my_skills, name="my_skills"),
    path("<int:pk>/", views.skill_detail, name="detail"),
    path("<int:pk>/edit/", views.skill_edit, name="edit"),
    path("<int:pk>/delete/", views.skill_delete, name="delete"),
    path("<int:pk>/watch/", views.toggle_watch, name="toggle_watch"),
]
