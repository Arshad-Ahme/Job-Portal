from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        REMOTE = 'remote', 'Remote'
        INTERNSHIP = 'internship', 'Internship'

    class Experience(models.TextChoices):
        FRESHER = 'fresher', 'Fresher'
        ONE_TO_THREE = '1-3', '1-3 years'
        THREE_TO_FIVE = '3-5', '3-5 years'
        FIVE_PLUS = '5+', '5+ years'

    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jobs',
        limit_choices_to={'role': 'recruiter'},
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='jobs'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    job_type = models.CharField(
        max_length=20, choices=JobType.choices, default=JobType.FULL_TIME
    )
    experience_level = models.CharField(
        max_length=10, choices=Experience.choices, default=Experience.FRESHER
    )
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company_name}"

    @property
    def company_name(self):
        return self.recruiter.recruiter_profile.company_name

    @property
    def is_open(self):
        return self.is_active and self.deadline >= timezone.now().date()


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'applied', 'Applied'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        REJECTED = 'rejected', 'Rejected'
        HIRED = 'hired', 'Hired'

    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name='applications'
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        limit_choices_to={'role': 'candidate'},
    )
    resume = models.FileField(upload_to='applications/resumes/')
    cover_letter = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.APPLIED
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_at']
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'candidate'],
                name='unique_application_per_job',
            )
        ]

    def __str__(self):
        return f"{self.candidate.username} -> {self.job.title}"


class SavedJob(models.Model):
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_jobs',
        limit_choices_to={'role': 'candidate'},
    )
    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name='saved_by'
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-saved_at']
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'job'],
                name='unique_saved_job',
            )
        ]

    def __str__(self):
        return f"{self.candidate.username} saved {self.job.title}"
