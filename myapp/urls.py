from django.urls import path
from .import views


urlpatterns = [
    path("", views.login_page, name="login"),
    path("admin_login", views.admin_login, name="admin_login"),
    path("student_login", views.student_login, name="student_login"),
    path("dashboard", views.Dashboard, name="dashboard"),
    path("logout", views.user_logout, name="logout"),
    path("create_student", views.create_student, name="create_student"),

    path("edit-profile", views.edit_profile, name="edit_profile"),
    path('student/<int:student_id>/projects/', views.view_student_projects, name='view_student_projects'),

     path('projects/all/', views.my_projects, name='my_projects'),
     path('project/<int:pk>/', views.project_detail, name='project_detail'),

     path('project/<int:project_id>/hire/', views.HireNowView, name='hire_now'),
     path('messages/', views.AllMessagesView, name='all_messages'),




]
