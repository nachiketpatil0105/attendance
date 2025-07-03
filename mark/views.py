from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib import messages
from .models import *


from collections import Counter
import calendar
from datetime import date, datetime
from calendar import monthrange

def parse_mixed_date(date_str):
    cleaned = date_str.replace(".", "").strip()

    try:
        return datetime.strptime(cleaned, "%B %d, %Y").date()
    except ValueError:
        return datetime.strptime(cleaned, "%b %d, %Y").date()

class RegisterUser(UserCreationForm):
  class Meta:
    model = User
    fields = ["username", "first_name", "password1", "password2"]

# Create your views here.
def index(request):
  if not request.user.is_authenticated:
    return redirect("login")
  
  today = date.today()
  context = {
    "user_data": Attend.objects.filter(user=request.user),
    "courses": Course.objects.filter(user=request.user),
    "today": today  # <== this line is important for course links
  }
  return render(request, "mark/index.html", context)

def sign_up(request):
  if request.user.is_authenticated:
    messages.error(request, "You Already Logged In")
    return redirect("index")
  if request.method == "POST":
    form = RegisterUser(request.POST)
    if form.is_valid():
      form.save()
      return redirect("login")
    else:
      return render(request, "mark/signup.html", {
        "form": form
      })
  else:
    form = RegisterUser()
    return render(request, "mark/signup.html", {
      "form": form
    })

def login_view(request):
  if request.user.is_authenticated:
    messages.error(request, "You are already logged in.")
    return redirect("index")

  if request.method == "POST":
    form = AuthenticationForm(request, data=request.POST)
    if form.is_valid():
      user = form.get_user()
      login(request, user)
      return redirect("index")
    else:
      # render with form including errors
      return render(request, "mark/login.html", {
        "form": form
      })
  else:
    form = AuthenticationForm()
    return render(request, "mark/login.html", {
      "form": form
    })

def logout_view(request):
  logout(request)
  messages.success(request, "Logged Out")
  return redirect("login")

def attendance_calendar(request, course, year = None, month = None):
  if not request.user.is_authenticated:
    return redirect("login")
  
  try:
    course_obj = Course.objects.get(user=request.user, course=course)
  except Course.DoesNotExist:
    messages.error(request, "Course not found")
    return redirect("index")

  if year is None or month is None:
    today = date.today()
    year = today.year
    month = today.month

  if month == 1:
    prev_month = 12
    prev_year = year - 1
  else:
    prev_month = month - 1
    prev_year = year

  if month == 12:
    next_month = 1
    next_year = year + 1
  else:
    next_month = month + 1
    next_year = year

  cal = calendar.Calendar(firstweekday=6)
  month_days = cal.itermonthdates(year, month)
  month_days_1 = list(cal.itermonthdates(year, month))


  records = Attend.objects.filter(user=request.user, date__date__year=year, date__date__month=month, course = course_obj)
  status_by_date = {a.date.date: a.status.status for a in records}

  # Summary stats
  all_statuses = [status_by_date.get(day, None) for day in month_days_1 if day.month == month]
  status_count = Counter(all_statuses)

  present = status_count.get("Present", 0)
  absent = status_count.get("Absent", 0)
  leave = status_count.get("Leave", 0)
  holiday = status_count.get("Holiday", 0)

  total_days = present + absent + leave
  attendance_percentage = round((present / total_days) * 100, 2) if total_days > 0 else 0.0

  # All-time records for the current user
  all_time_records = Attend.objects.filter(user=request.user, course = course_obj)
  all_time_statuses = [record.status.status for record in all_time_records]

  # Count each status
  all_time_counts = Counter(all_time_statuses)

  all_time_present = all_time_counts.get("Present", 0)
  all_time_absent = all_time_counts.get("Absent", 0)
  all_time_leave = all_time_counts.get("Leave", 0)
  all_time_holiday = all_time_counts.get("Holiday", 0)

  all_time_total = all_time_present + all_time_absent + all_time_leave
  all_time_percentage = round((all_time_present / all_time_total) * 100, 2) if all_time_total > 0 else 0.0

  context = {
    'course': course,
    'year': year,
    'month': month,
    "prev_month": prev_month,
    "prev_year": prev_year,
    "next_month": next_month,
    "next_year": next_year,
    'month_name': calendar.month_name[month],
    'days': [(day, status_by_date.get(day)) for day in month_days],
    'statuses': ["Present", "Absent", "Leave", "Holiday", "Clear"],
    'summary': {
      'present': present,
      'absent': absent,
      'leave': leave,
      'holiday': holiday,
      'total_days': total_days,
      'attendance_percentage': attendance_percentage
    },
    'all_time_summary': {
      'present': all_time_present,
      'absent': all_time_absent,
      'leave': all_time_leave,
      'holiday': all_time_holiday,
      'total_days': all_time_total,
      'attendance_percentage': all_time_percentage
    }
  }
  return render(request, 'mark/calendar.html', context)

def save_attend(request):
  if request.method == "POST":
    date_str = request.POST["date"]       
    status_str = request.POST["status"]   
    course_str = request.POST["course"]
    user = request.user

    course_obj = Course.objects.get(user=user, course=course_str)
    try:
      course_obj = Course.objects.get(user=user, course=course_str)
    except Course.DoesNotExist:
      messages.error(request, "Invalid course")
      return redirect("index")
    
    date_obj = parse_mixed_date(date_str)

    date_instance, _ = Date.objects.get_or_create(date=date_obj)

    if status_str != "Clear":
      status_instance, _ = Status.objects.get_or_create(status=status_str)

      Attend.objects.update_or_create(
          user=user,
          date=date_instance,
          course = course_obj,
          defaults={"status": status_instance}
      )
    else:
      Attend.objects.filter(user=user, date=date_instance, course=course_obj).delete()

      if not Attend.objects.filter(date=date_instance).exists():
        date_instance.delete()

    return redirect("attendance_calendar", course=course_str, year = date_obj.year, month = date_obj.month)
  
def course_add(request):
  if request.method == "POST":
    course_name = request.POST["course_name"]
    user_name = request.user
    Course.objects.create(user = user_name, course = course_name)
  return redirect("index")

def delete_course(request, course_name):
    if request.user.is_authenticated:
        try:
            course = Course.objects.get(user=request.user, course=course_name)
            course.delete()
            messages.success(request, f"Course '{course_name}' deleted.")
        except Course.DoesNotExist:
            messages.error(request, "Course not found.")
    else:
        messages.error(request, "You must be logged in to delete courses.")
    return redirect("index")


