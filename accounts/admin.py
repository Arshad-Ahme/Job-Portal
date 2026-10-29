# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, CandidateProfile, RecruiterProfile


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Role', {'fields': ('role',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Role', {'fields': ('role',)}),)
    list_display = ['username', 'email', 'role', 'is_staff']

admin.site.register(User, CustomUserAdmin)


class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'location']

admin.site.register(CandidateProfile, CandidateProfileAdmin)


class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'website']

admin.site.register(RecruiterProfile, RecruiterProfileAdmin)