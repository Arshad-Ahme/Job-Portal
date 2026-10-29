from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect

from .forms import (
    SignUpForm, UserBasicForm, CandidateProfileForm, RecruiterProfileForm,
)
from .models import CandidateProfile, RecruiterProfile


def is_candidate(user):
    return user.is_authenticated and user.is_candidate


def is_recruiter(user):
    return user.is_authenticated and user.is_recruiter


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account was created. Welcome!')
            return redirect('dashboard')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def dashboard(request):
    if request.user.is_recruiter:
        return redirect('recruiter_dashboard')
    return redirect('candidate_dashboard')


@user_passes_test(is_candidate)
def candidate_dashboard(request):
    return render(request, 'accounts/candidate_dashboard.html')


@user_passes_test(is_recruiter)
def recruiter_dashboard(request):
    return render(request, 'accounts/recruiter_dashboard.html')


@login_required
def profile_edit(request):
    user = request.user

    if user.is_recruiter:
        profile, _ = RecruiterProfile.objects.get_or_create(
            user=user, defaults={'company_name': ''}
        )
        profile_form_class = RecruiterProfileForm
    else:
        profile, _ = CandidateProfile.objects.get_or_create(user=user)
        profile_form_class = CandidateProfileForm

    if request.method == 'POST':
        user_form = UserBasicForm(request.POST, instance=user)
        profile_form = profile_form_class(
            request.POST, request.FILES, instance=profile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile_edit')
    else:
        user_form = UserBasicForm(instance=user)
        profile_form = profile_form_class(instance=profile)

    return render(request, 'accounts/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })