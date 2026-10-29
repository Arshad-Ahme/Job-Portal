import os

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, CandidateProfile, RecruiterProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.RadioSelect,
        initial=User.Role.CANDIDATE,
    )
    company_name = forms.CharField(
        max_length=150,
        required=False,
        help_text="Required if you are a recruiter",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role')

    field_order = [
        'username', 'email', 'role', 'company_name', 'password1', 'password2'
    ]

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        company = cleaned_data.get('company_name')
        if role == User.Role.RECRUITER and not company:
            self.add_error('company_name', 'Company name is required for recruiters.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save()
        if user.role == User.Role.RECRUITER:
            RecruiterProfile.objects.create(
                user=user, company_name=self.cleaned_data['company_name']
            )
        else:
            CandidateProfile.objects.create(user=user)
        return user


class UserBasicForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ['phone', 'location', 'skills', 'bio', 'resume']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'skills': forms.TextInput(attrs={'placeholder': 'Python, Django, SQL'}),
        }

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume and hasattr(resume, 'content_type'):
            extension = os.path.splitext(resume.name)[1].lower()
            if extension not in ['.pdf', '.doc', '.docx']:
                raise forms.ValidationError('Upload a PDF or Word document.')
            if resume.size > 2 * 1024 * 1024:
                raise forms.ValidationError('Resume must be smaller than 2 MB.')
        return resume


class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        fields = ['company_name', 'website', 'description', 'logo']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo and hasattr(logo, 'content_type') and logo.size > 1024 * 1024:
            raise forms.ValidationError('Logo must be smaller than 1 MB.')
        return logo
