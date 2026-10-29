from django.test import TestCase

# Create your tests here.
import shutil
import tempfile
from datetime import timedelta

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.tests import PASSWORD, create_candidate, create_recruiter
from .models import Application, Category, Job, SavedJob

TEMP_MEDIA = tempfile.mkdtemp()


def tearDownModule():
    shutil.rmtree(TEMP_MEDIA, ignore_errors=True)


def create_job(recruiter, category, **kwargs):
    defaults = {
        'title': 'Python Developer',
        'description': 'Build APIs.',
        'location': 'Mumbai',
        'job_type': Job.JobType.FULL_TIME,
        'experience_level': Job.Experience.FRESHER,
        'deadline': timezone.now().date() + timedelta(days=30),
    }
    defaults.update(kwargs)
    return Job.objects.create(recruiter=recruiter, category=category, **defaults)


def pdf_file(name='resume.pdf'):
    return SimpleUploadedFile(name, b'%PDF-1.4 test resume',
                              content_type='application/pdf')


class JobModelTests(TestCase):
    def setUp(self):
        self.recruiter = create_recruiter()
        self.category = Category.objects.create(name='Software')

    def test_active_job_with_future_deadline_is_open(self):
        job = create_job(self.recruiter, self.category)
        self.assertTrue(job.is_open)

    def test_inactive_job_is_not_open(self):
        job = create_job(self.recruiter, self.category, is_active=False)
        self.assertFalse(job.is_open)

    def test_expired_job_is_not_open(self):
        job = create_job(
            self.recruiter, self.category,
            deadline=timezone.now().date() - timedelta(days=1),
        )
        self.assertFalse(job.is_open)

    def test_company_name_comes_from_recruiter_profile(self):
        job = create_job(self.recruiter, self.category)
        self.assertEqual(job.company_name, 'Acme Ltd')


class JobListTests(TestCase):
    def setUp(self):
        self.recruiter = create_recruiter()
        self.category = Category.objects.create(name='Software')

    def test_open_job_is_listed(self):
        create_job(self.recruiter, self.category, title='Visible Job')
        response = self.client.get(reverse('job_list'))
        self.assertContains(response, 'Visible Job')

    def test_closed_job_is_hidden(self):
        create_job(self.recruiter, self.category,
                   title='Hidden Closed Job', is_active=False)
        response = self.client.get(reverse('job_list'))
        self.assertNotContains(response, 'Hidden Closed Job')

    def test_expired_job_is_hidden(self):
        create_job(
            self.recruiter, self.category, title='Hidden Expired Job',
            deadline=timezone.now().date() - timedelta(days=1),
        )
        response = self.client.get(reverse('job_list'))
        self.assertNotContains(response, 'Hidden Expired Job')

    def test_search_filters_by_title(self):
        create_job(self.recruiter, self.category, title='Django Developer')
        create_job(self.recruiter, self.category, title='Data Analyst')
        response = self.client.get(reverse('job_list'), {'q': 'django'})
        self.assertContains(response, 'Django Developer')
        self.assertNotContains(response, 'Data Analyst')

    def test_filter_by_category(self):
        design = Category.objects.create(name='Design')
        create_job(self.recruiter, self.category, title='Backend Engineer')
        create_job(self.recruiter, design, title='Logo Designer')
        response = self.client.get(reverse('job_list'), {'category': design.id})
        self.assertContains(response, 'Logo Designer')
        self.assertNotContains(response, 'Backend Engineer')

    def test_pagination_shows_six_per_page(self):
        for i in range(7):
            create_job(self.recruiter, self.category, title=f'Job number {i}')
        page1 = self.client.get(reverse('job_list'))
        page2 = self.client.get(reverse('job_list'), {'page': 2})
        self.assertEqual(len(page1.context['page_obj'].object_list), 6)
        self.assertEqual(len(page2.context['page_obj'].object_list), 1)


class JobDetailTests(TestCase):
    def setUp(self):
        self.recruiter = create_recruiter()
        self.category = Category.objects.create(name='Software')
        self.job = create_job(self.recruiter, self.category)

    def test_detail_page_loads(self):
        response = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertContains(response, 'Python Developer')

    def test_anonymous_user_sees_login_to_apply(self):
        response = self.client.get(reverse('job_detail', args=[self.job.pk]))
        self.assertContains(response, 'Login to apply')

    def test_missing_job_returns_404(self):
        response = self.client.get(reverse('job_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)


class RecruiterJobTests(TestCase):
    def setUp(self):
        self.recruiter = create_recruiter()
        self.other = create_recruiter(
            username='recruiter2', email='recruiter2@example.com',
            company='Globex',
        )
        self.candidate = create_candidate()
        self.category = Category.objects.create(name='Software')

    def job_data(self, **overrides):
        data = {
            'title': 'New Job',
            'category': self.category.id,
            'description': 'Do great work.',
            'location': 'Delhi',
            'job_type': 'full_time',
            'experience_level': 'fresher',
            'salary_min': '',
            'salary_max': '',
            'deadline': (timezone.now().date() + timedelta(days=10)).isoformat(),
            'is_active': 'on',
        }
        data.update(overrides)
        return data

    def test_recruiter_can_post_job(self):
        self.client.login(username='recruiter1', password=PASSWORD)
        response = self.client.post(reverse('job_create'), self.job_data())
        self.assertRedirects(
            response, reverse('my_jobs'), fetch_redirect_response=False
        )
        job = Job.objects.get(title='New Job')
        self.assertEqual(job.recruiter, self.recruiter)

    def test_past_deadline_is_rejected(self):
        self.client.login(username='recruiter1', password=PASSWORD)
        yesterday = (timezone.now().date() - timedelta(days=1)).isoformat()
        response = self.client.post(
            reverse('job_create'), self.job_data(deadline=yesterday)
        )
        self.assertContains(response, 'Deadline cannot be in the past.')
        self.assertEqual(Job.objects.count(), 0)

    def test_max_salary_below_min_is_rejected(self):
        self.client.login(username='recruiter1', password=PASSWORD)
        response = self.client.post(
            reverse('job_create'),
            self.job_data(salary_min='500000', salary_max='300000'),
        )
        self.assertContains(
            response, 'Maximum salary cannot be less than minimum.'
        )
        self.assertEqual(Job.objects.count(), 0)

    def test_candidate_cannot_post_job(self):
        self.client.login(username='candidate1', password=PASSWORD)
        response = self.client.get(reverse('job_create'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_recruiter_cannot_edit_another_recruiters_job(self):
        job = create_job(self.other, self.category)
        self.client.login(username='recruiter1', password=PASSWORD)
        response = self.client.get(reverse('job_edit', args=[job.pk]))
        self.assertEqual(response.status_code, 404)

    def test_recruiter_can_edit_own_job(self):
        job = create_job(self.recruiter, self.category)
        self.client.login(username='recruiter1', password=PASSWORD)
        response = self.client.post(
            reverse('job_edit', args=[job.pk]),
            self.job_data(title='Updated Title'),
        )
        self.assertRedirects(
            response, reverse('my_jobs'), fetch_redirect_response=False
        )
        job.refresh_from_db()
        self.assertEqual(job.title, 'Updated Title')

    def test_toggle_closes_and_reopens_job(self):
        job = create_job(self.recruiter, self.category)
        self.client.login(username='recruiter1', password=PASSWORD)
        self.client.post(reverse('job_toggle', args=[job.pk]))
        job.refresh_from_db()
        self.assertFalse(job.is_active)
        self.client.post(reverse('job_toggle', args=[job.pk]))
        job.refresh_from_db()
        self.assertTrue(job.is_active)

    def test_toggle_requires_post(self):
        job = create_job(self.recruiter, self.category)
        self.client.login(username='recruiter1', password=PASSWORD)
        response = self.client.get(reverse('job_toggle', args=[job.pk]))
        self.assertEqual(response.status_code, 405)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ApplicationTests(TestCase):
    def setUp(self):
        self.recruiter = create_recruiter()
        self.other = create_recruiter(
            username='recruiter2', email='recruiter2@example.com',
            company='Globex',
        )
        self.candidate = create_candidate()
        self.category = Category.objects.create(name='Software')
        self.job = create_job(self.recruiter, self.category)

    def apply(self, **overrides):
        data = {'resume': pdf_file(), 'cover_letter': 'Please hire me.'}
        data.update(overrides)
        return self.client.post(reverse('apply_job', args=[self.job.pk]), data)

    def make_application(self):
        return Application.objects.create(
            job=self.job, candidate=self.candidate,
            resume='applications/resumes/test.pdf',
        )

    def test_candidate_can_apply(self):
        self.client.login(username='candidate1', password=PASSWORD)
        response = self.apply()
        self.assertRedirects(
            response, reverse('my_applications'), fetch_redirect_response=False
        )
        self.assertEqual(
            Application.objects.filter(
                job=self.job, candidate=self.candidate
            ).count(),
            1,
        )

    def test_recruiter_is_emailed_about_new_application(self):
        self.client.login(username='candidate1', password=PASSWORD)
        self.apply()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('New application', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, [self.recruiter.email])

    def test_cannot_apply_twice(self):
        self.client.login(username='candidate1', password=PASSWORD)
        self.apply()
        self.apply(resume=pdf_file('second.pdf'))
        self.assertEqual(Application.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_invalid_resume_type_is_rejected(self):
            self.client.login(username='candidate1', password=PASSWORD)
            photo = SimpleUploadedFile('photo.png', b'not a resume',
                                       content_type='image/png')
            response = self.apply(resume=photo)
            self.assertContains(response, 'Upload a PDF or Word document.')
            self.assertEqual(Application.objects.count(), 0)

    def test_recruiter_cannot_apply(self):
            self.client.login(username='recruiter2', password=PASSWORD)
            response = self.apply()
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse('login')))
            self.assertEqual(Application.objects.count(), 0)

    def test_cannot_apply_to_closed_job(self):
            self.job.is_active = False
            self.job.save()
            self.client.login(username='candidate1', password=PASSWORD)
            response = self.apply()
            self.assertRedirects(
                response, reverse('job_detail', args=[self.job.pk]),
                fetch_redirect_response=False,
            )
            self.assertEqual(Application.objects.count(), 0)

    def test_recruiter_can_change_status_and_candidate_is_emailed(self):
            application = self.make_application()
            self.client.login(username='recruiter1', password=PASSWORD)
            self.client.post(
                reverse('update_application_status', args=[application.pk]),
                {'status': 'shortlisted'},
            )
            application.refresh_from_db()
            self.assertEqual(application.status, 'shortlisted')
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn('Update on your application', mail.outbox[0].subject)
            self.assertEqual(mail.outbox[0].to, [self.candidate.email])

    def test_same_status_sends_no_email(self):
            application = self.make_application()
            self.client.login(username='recruiter1', password=PASSWORD)
            self.client.post(
                reverse('update_application_status', args=[application.pk]),
                {'status': 'applied'},
            )
            self.assertEqual(len(mail.outbox), 0)

    def test_invalid_status_is_ignored(self):
            application = self.make_application()
            self.client.login(username='recruiter1', password=PASSWORD)
            self.client.post(
                reverse('update_application_status', args=[application.pk]),
                {'status': 'bogus'},
            )
            application.refresh_from_db()
            self.assertEqual(application.status, 'applied')

    def test_other_recruiter_cannot_change_status(self):
            application = self.make_application()
            self.client.login(username='recruiter2', password=PASSWORD)
            response = self.client.post(
                reverse('update_application_status', args=[application.pk]),
                {'status': 'hired'},
            )
            self.assertEqual(response.status_code, 404)
            application.refresh_from_db()
            self.assertEqual(application.status, 'applied')

    def test_candidate_cannot_change_status(self):
            application = self.make_application()
            self.client.login(username='candidate1', password=PASSWORD)
            response = self.client.post(
                reverse('update_application_status', args=[application.pk]),
                {'status': 'hired'},
            )
            self.assertEqual(response.status_code, 302)
            application.refresh_from_db()
            self.assertEqual(application.status, 'applied')

    def test_owner_recruiter_can_see_applicants_page(self):
            self.make_application()
            self.client.login(username='recruiter1', password=PASSWORD)
            response = self.client.get(
                reverse('job_applicants', args=[self.job.pk])
            )
            self.assertContains(response, 'candidate1')

    def test_other_recruiter_cannot_see_applicants_page(self):
            self.client.login(username='recruiter2', password=PASSWORD)
            response = self.client.get(
                reverse('job_applicants', args=[self.job.pk])
            )
            self.assertEqual(response.status_code, 404)

class SavedJobTests(TestCase):
        def setUp(self):
            self.recruiter = create_recruiter()
            self.candidate = create_candidate()
            self.category = Category.objects.create(name='Software')
            self.job = create_job(self.recruiter, self.category)

        def test_candidate_can_save_and_unsave_job(self):
            self.client.login(username='candidate1', password=PASSWORD)
            url = reverse('toggle_save_job', args=[self.job.pk])
            self.client.post(url)
            self.assertEqual(SavedJob.objects.count(), 1)
            self.client.post(url)
            self.assertEqual(SavedJob.objects.count(), 0)

        def test_saved_jobs_page_lists_saved_job(self):
            SavedJob.objects.create(candidate=self.candidate, job=self.job)
            self.client.login(username='candidate1', password=PASSWORD)
            response = self.client.get(reverse('saved_jobs'))
            self.assertContains(response, 'Python Developer')

        def test_recruiter_cannot_save_job(self):
            self.client.login(username='recruiter1', password=PASSWORD)
            response = self.client.post(
                reverse('toggle_save_job', args=[self.job.pk])
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(SavedJob.objects.count(), 0)

    
