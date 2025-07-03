from django.urls import path
from . import views

urlpatterns = [
  path("/", views.index, name="index"),
  path("login/", views.login_view, name="login"),
  path("logout/", views.logout_view, name="logout"),
  path("signup/", views.sign_up, name="signup"),
  path("saveattend/", views.save_attend, name="saveattend"),
  path("addcourse/", views.course_add, name="course_add"),
  path("delete/<str:course_name>/", views.delete_course, name="delete_course"),
  path('<str:course>/<int:year>/<int:month>/', views.attendance_calendar, name='attendance_calendar'),
]