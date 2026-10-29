from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.urls import reverse

from .models import User, CandidateProfile, RecruiterProfile

PASSWORD = 'Str0ng!Pass_987'


def create_candidate(username='candidate1', email='candidate1@example.com'):
    user = User.objects.create_user(
        username=username, email=email, password=PASSWORD,
        role=User.Role.CANDIDATE,
    )
    CandidateProfile.objects.create(user=user)
    return user


def create_recruiter(username='recruiter1', email='recruiter1@example.com',
                     company='Acme Ltd'):
    user = User.objects.create_user(
        username=username, email=email, password=PASSWORD,
        role=User.Role.RECRUITER,
    )
    RecruiterProfile.objects.create(user=user, company_name=company)
    return user


class SignUpTests(TestCase):
    def signup_data(self, **overrides):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'role': 'candidate',
            'company_name': '',
            'password1': PASSWORD,
            'password2': PASSWORD,
        }
        data.update(overrides)
        return data

    def test_signup_page_loads(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_candidate_signup_creates_user_and_profile(self):
        response = self.client.post(reverse('signup'), self.signup_data())
        user = User.objects.get(username='newuser')
        self.assertEqual(user.role, User.Role.CANDIDATE)
        self.assertTrue(CandidateProfile.objects.filter(user=user).exists())
        self.assertRedirects(
            response, reverse('dashboard'), fetch_redirect_response=False
        )

    def test_recruiter_signup_creates_recruiter_profile(self):
        self.client.post(
            reverse('signup'),
            self.signup_data(
                username='boss', role='recruiter', company_name='Globex'
            ),
        )
        user = User.objects.get(username='boss')
        self.assertEqual(user.role, User.Role.RECRUITER)
        self.assertEqual(user.recruiter_profile.company_name, 'Globex')

    def test_recruiter_signup_requires_company_name(self):
        response = self.client.post(
            reverse('signup'),
            self.signup_data(username='boss', role='recruiter'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Company name is required for recruiters.')
        self.assertFalse(User.objects.filter(username='boss').exists())

    def test_password_mismatch_does_not_create_user(self):
        response = self.client.post(
            reverse('signup'),
            self.signup_data(password2='Different!Pass_123'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_logged_in_user_is_redirected_away_from_signup(self):
        create_candidate()
        self.client.login(username='candidate1', password=PASSWORD)
        response = self.client.get(reverse('signup'))
        self.assertRedirects(
            response, reverse('dashboard'), fetch_redirect_response=False
        )


class RoleAccessTests(TestCase):
    def setUp(self):
        self.candidate = create_candidate()
        self.recruiter = create_recruiter()

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard')}",
            fetch_redirect_response=False,
        )

    def test_dashboard_redirects_candidate(self):
        self.client.login(username='candidate1', password=PASSWORD)
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(
            response, reverse('candidate_dashboard'),
            fetch_redirect_response=False,
        )

    def test_dashboard_redirects_recruiter(self):
        self.client.login(username='recruiter1', password=PASSWORD)
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(
            response, reverse('recruiter_dashboard'),
            fetch_redirect_response=False,
        )

    def test_candidate_cannot_open_recruiter_dashboard(self):
        self.client.login(username='candidate1', password=PASSWORD)
        response = self.client.get(reverse('recruiter_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_recruiter_cannot_open_candidate_dashboard(self):
        self.client.login(username='recruiter1', password=PASSWORD)
        response = self.client.get(reverse('candidate_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_candidate_dashboard_loads_for_candidate(self):
        self.client.login(username='candidate1', password=PASSWORD)
        response = self.client.get(reverse('candidate_dashboard'))
        self.assertEqual(response.status_code, 200)


class ProfileTests(TestCase):
    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_candidate_can_update_profile(self):
        candidate = create_candidate()
        self.client.login(username='candidate1', password=PASSWORD)
        response = self.client.post(reverse('profile_edit'), {
            'first_name': 'Arshad',
            'last_name': 'Khan',
            'email': 'new@example.com',
            'phone': '9876543210',
            'location': 'Pune',
            'skills': 'Python, Django',
            'bio': 'Backend developer',
        })
        self.assertRedirects(
            response, reverse('profile_edit'), fetch_redirect_response=False
        )
        candidate.refresh_from_db()
        candidate.candidate_profile.refresh_from_db()
        self.assertEqual(candidate.first_name, 'Arshad')
        self.assertEqual(candidate.email, 'new@example.com')
        self.assertEqual(candidate.candidate_profile.phone, '9876543210')

    def test_recruiter_can_update_company(self):
        recruiter = create_recruiter()
        self.client.login(username='recruiter1', password=PASSWORD)
        response = self.client.post(reverse('profile_edit'), {
            'first_name': 'Sara',
            'last_name': 'Ali',
            'email': 'sara@example.com',
            'company_name': 'Initech',
            'website': 'https://initech.example.com',
            'description': 'We build software.',
        })
        self.assertRedirects(
            response, reverse('profile_edit'), fetch_redirect_response=False
        )
        recruiter.recruiter_profile.refresh_from_db()
        self.assertEqual(recruiter.recruiter_profile.company_name, 'Initech')