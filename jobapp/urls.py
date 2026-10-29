from django.urls import path

from . import views

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/apply/', views.apply_job, name='apply_job'),
    path('<int:pk>/save/', views.toggle_save_job, name='toggle_save_job'),
    path('saved/', views.saved_jobs, name='saved_jobs'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('post/', views.job_create, name='job_create'),
    path('<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('<int:pk>/toggle/', views.job_toggle, name='job_toggle'),
    path('<int:pk>/applicants/', views.job_applicants, name='job_applicants'),
    path('applications/<int:pk>/status/', views.update_application_status,
         name='update_application_status'),
]