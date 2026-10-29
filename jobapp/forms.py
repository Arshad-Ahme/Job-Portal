import os

from django import forms
from django.utils import timezone

from .models import Job, Application


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'category', 'description', 'location',
            'job_type', 'experience_level',
            'salary_min', 'salary_max', 'deadline', 'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data['deadline']
        if deadline < timezone.now().date():
            raise forms.ValidationError('Deadline cannot be in the past.')
        return deadline

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        if salary_min and salary_max and salary_max < salary_min:
            self.add_error('salary_max', 'Maximum salary cannot be less than minimum.')
        return cleaned_data


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume', 'cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_resume(self):
        resume = self.cleaned_data['resume']
        extension = os.path.splitext(resume.name)[1].lower()
        if extension not in ['.pdf', '.doc', '.docx']:
            raise forms.ValidationError('Upload a PDF or Word document.')
        if resume.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Resume must be smaller than 2 MB.')
        return resume

