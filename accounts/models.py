# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CANDIDATE = 'candidate', 'Candidate'
        RECRUITER = 'recruiter', 'Recruiter'

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.CANDIDATE
    )

    @property
    def is_candidate(self):
        return self.role == self.Role.CANDIDATE

    @property
    def is_recruiter(self):
        return self.role == self.Role.RECRUITER

    def __str__(self):
        return f"{self.username} ({self.role})"


class CandidateProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='candidate_profile'
    )
    phone = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)
    skills = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)

    def __str__(self):
        return f"Candidate: {self.user.username}"


class RecruiterProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='recruiter_profile'
    )
    company_name = models.CharField(max_length=150)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)

    def __str__(self):
        return f"Recruiter: {self.company_name}"
