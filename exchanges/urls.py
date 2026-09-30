from django.urls import path

from exchanges import views

app_name = "exchanges"

urlpatterns = [
    path("", views.exchange_list, name="list"),
    path("new/<int:skill_pk>/", views.exchange_create, name="create"),
    path("sent/", views.exchange_sent, name="sent"),
    path("received/", views.exchange_received, name="received"),
    path("history/", views.exchange_history, name="history"),
    path("report/", views.report_create, name="report_create"),
    path("<int:pk>/", views.exchange_detail, name="detail"),
    path("<int:pk>/review/", views.exchange_review, name="review"),
]
