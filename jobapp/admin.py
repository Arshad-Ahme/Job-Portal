from django.contrib import admin

from .models import Category, Job, Application, SavedJob


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


admin.site.register(Category, CategoryAdmin)


class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'recruiter', 'category', 'location',
                    'job_type', 'deadline', 'is_active']
    list_filter = ['job_type', 'category', 'is_active']
    search_fields = ['title', 'location']


admin.site.register(Job, JobAdmin)


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'candidate', 'status', 'applied_at']
    list_filter = ['status']


admin.site.register(Application, ApplicationAdmin)


class SavedJobAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job', 'saved_at']


admin.site.register(SavedJob, SavedJobAdmin)
