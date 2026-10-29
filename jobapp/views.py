from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.views import is_candidate, is_recruiter
from .emails import send_new_application_email, send_status_email
from .forms import JobForm, ApplicationForm
from .models import Category, Job, Application, SavedJob


def job_list(request):
    jobs = Job.objects.filter(
        is_active=True, deadline__gte=timezone.now().date()
    ).select_related('category', 'recruiter__recruiter_profile')

    q = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()
    category = request.GET.get('category', '')
    job_type = request.GET.get('job_type', '')
    experience = request.GET.get('experience', '')

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(recruiter__recruiter_profile__company_name__icontains=q)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if category.isdigit():
        jobs = jobs.filter(category_id=category)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if experience:
        jobs = jobs.filter(experience_level=experience)

    paginator = Paginator(jobs, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    params = request.GET.copy()
    params.pop('page', None)

    return render(request, 'jobapp/job_list.html', {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'job_types': Job.JobType.choices,
        'experience_levels': Job.Experience.choices,
        'query_string': params.urlencode(),
        'q': q,
        'location': location,
        'selected_category': category,
        'selected_job_type': job_type,
        'selected_experience': experience,
    })


def job_detail(request, pk):
    job = get_object_or_404(
        Job.objects.select_related('category', 'recruiter__recruiter_profile'),
        pk=pk,
    )
    already_applied = False
    is_saved = False
    if request.user.is_authenticated and request.user.is_candidate:
        already_applied = Application.objects.filter(
            job=job, candidate=request.user
        ).exists()
        is_saved = SavedJob.objects.filter(
            job=job, candidate=request.user
        ).exists()
    return render(request, 'jobapp/job_detail.html', {
        'job': job,
        'already_applied': already_applied,
        'is_saved': is_saved,
    })


@user_passes_test(is_candidate)
def apply_job(request, pk):
    job = get_object_or_404(Job, pk=pk)

    if not job.is_open:
        messages.error(request, 'This job is no longer accepting applications.')
        return redirect('job_detail', pk=job.pk)

    if Application.objects.filter(job=job, candidate=request.user).exists():
        messages.info(request, 'You have already applied for this job.')
        return redirect('my_applications')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.candidate = request.user
            application.save()
            send_new_application_email(application)
            messages.success(request, 'Application submitted successfully.')
            return redirect('my_applications')
    else:
        form = ApplicationForm()

    return render(request, 'jobapp/apply.html', {'form': form, 'job': job})


@user_passes_test(is_candidate)
def my_applications(request):
    applications = Application.objects.filter(
        candidate=request.user
    ).select_related('job', 'job__recruiter__recruiter_profile')
    return render(request, 'jobapp/my_applications.html', {
        'applications': applications,
    })


@user_passes_test(is_candidate)
@require_POST
def toggle_save_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    saved, created = SavedJob.objects.get_or_create(
        candidate=request.user, job=job
    )
    if created:
        messages.success(request, 'Job saved.')
    else:
        saved.delete()
        messages.info(request, 'Removed from saved jobs.')

    if request.POST.get('next') == 'saved_jobs':
        return redirect('saved_jobs')
    return redirect('job_detail', pk=job.pk)


@user_passes_test(is_candidate)
def saved_jobs(request):
    saved = SavedJob.objects.filter(
        candidate=request.user
    ).select_related('job', 'job__category', 'job__recruiter__recruiter_profile')
    return render(request, 'jobapp/saved_jobs.html', {'saved_jobs': saved})


@user_passes_test(is_recruiter)
def my_jobs(request):
    jobs = Job.objects.filter(
        recruiter=request.user
    ).select_related('category').annotate(
        applicant_count=Count('applications')
    )
    return render(request, 'jobapp/my_jobs.html', {'jobs': jobs})


@user_passes_test(is_recruiter)
def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.save()
            messages.success(request, 'Job posted successfully.')
            return redirect('my_jobs')
    else:
        form = JobForm()
    return render(request, 'jobapp/job_form.html', {
        'form': form,
        'page_title': 'Post a Job',
    })


@user_passes_test(is_recruiter)
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully.')
            return redirect('my_jobs')
    else:
        form = JobForm(instance=job)
    return render(request, 'jobapp/job_form.html', {
        'form': form,
        'page_title': 'Edit Job',
    })


@user_passes_test(is_recruiter)
@require_POST
def job_toggle(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    job.is_active = not job.is_active
    job.save()
    state = 'reopened' if job.is_active else 'closed'
    messages.success(request, f'Job "{job.title}" {state}.')
    return redirect('my_jobs')


@user_passes_test(is_recruiter)
def job_applicants(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    applications = job.applications.select_related('candidate__candidate_profile')
    return render(request, 'jobapp/applicants.html', {
        'job': job,
        'applications': applications,
        'statuses': Application.Status.choices,
    })


@user_passes_test(is_recruiter)
@require_POST
def update_application_status(request, pk):
    application = get_object_or_404(
        Application, pk=pk, job__recruiter=request.user
    )
    new_status = request.POST.get('status')
    if new_status in Application.Status.values:
        if new_status != application.status:
            application.status = new_status
            application.save()
            send_status_email(application)
            messages.success(
                request,
                f'{application.candidate.username} marked as '
                f'{application.get_status_display()}.'
            )
        else:
            messages.info(request, 'Status was not changed.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect('job_applicants', pk=application.job.pk)