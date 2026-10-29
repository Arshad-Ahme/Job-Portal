import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from accounts.models import User, CandidateProfile, RecruiterProfile
from jobapp.models import Category, Job

PASSWORD = 'Demo@12345'

CATEGORY_TITLES = {
    'Software Development': [
        'Python Developer', 'Django Backend Developer', 'Full Stack Developer',
        'Java Developer', 'Frontend Developer', 'DevOps Engineer', 'QA Engineer',
    ],
    'Data Science': [
        'Data Analyst', 'Data Scientist', 'Machine Learning Engineer',
        'Business Intelligence Analyst',
    ],
    'Design': [
        'UI/UX Designer', 'Graphic Designer', 'Product Designer',
    ],
    'Marketing': [
        'Digital Marketing Executive', 'SEO Specialist', 'Content Writer',
        'Social Media Manager',
    ],
    'Finance': [
        'Accountant', 'Financial Analyst', 'Audit Associate',
    ],
    'Human Resources': [
        'HR Executive', 'Talent Acquisition Specialist', 'HR Manager',
    ],
}

SKILLS = [
    'Python', 'Django', 'SQL', 'JavaScript', 'HTML', 'CSS', 'Bootstrap',
    'Git', 'REST APIs', 'PostgreSQL', 'Docker', 'Excel', 'Communication',
]


class Command(BaseCommand):
    help = 'Fill the database with fake recruiters, candidates and jobs'

    def add_arguments(self, parser):
        parser.add_argument('--recruiters', type=int, default=8)
        parser.add_argument('--candidates', type=int, default=15)
        parser.add_argument('--jobs', type=int, default=40)
        parser.add_argument('--clear', action='store_true',
                            help='Delete earlier demo users (and their jobs) first')

    def handle(self, *args, **options):
        fake = Faker('en_IN')  # change to 'en_US' for US-style names and cities

        if options['clear']:
            deleted, _ = User.objects.filter(username__startswith='demo_').delete()
            self.stdout.write(f'Removed {deleted} old demo records')

        categories = [
            Category.objects.get_or_create(name=name)[0]
            for name in CATEGORY_TITLES
        ]

        recruiters = []
        for i in range(1, options['recruiters'] + 1):
            user, created = User.objects.get_or_create(
                username=f'demo_recruiter{i}',
                defaults={
                    'email': f'demo_recruiter{i}@example.com',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'role': User.Role.RECRUITER,
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
                RecruiterProfile.objects.create(
                    user=user,
                    company_name=fake.company(),
                    website=f'https://www.{fake.domain_name()}',
                    description=fake.paragraph(nb_sentences=3),
                )
            recruiters.append(user)

        for i in range(1, options['candidates'] + 1):
            user, created = User.objects.get_or_create(
                username=f'demo_candidate{i}',
                defaults={
                    'email': f'demo_candidate{i}@example.com',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'role': User.Role.CANDIDATE,
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
                CandidateProfile.objects.create(
                    user=user,
                    phone=fake.msisdn()[:10],
                    location=fake.city(),
                    skills=', '.join(random.sample(SKILLS, 5)),
                    bio=fake.paragraph(nb_sentences=3),
                )

        today = timezone.now().date()
        for _ in range(options['jobs']):
            category = random.choice(categories)
            salary_min = random.randrange(300000, 1500000, 50000)
            show_salary = random.random() > 0.2
            Job.objects.create(
                recruiter=random.choice(recruiters),
                category=category,
                title=random.choice(CATEGORY_TITLES[category.name]),
                description='\n\n'.join(fake.paragraphs(nb=3)),
                location=fake.city(),
                job_type=random.choice(Job.JobType.values),
                experience_level=random.choice(Job.Experience.values),
                salary_min=salary_min if show_salary else None,
                salary_max=(salary_min + random.randrange(100000, 500000, 50000))
                if show_salary else None,
                deadline=today + timedelta(days=random.randint(-10, 60)),
                is_active=random.random() > 0.1,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Created {options['jobs']} jobs, {options['recruiters']} recruiters "
            f"and {options['candidates']} candidates."
        ))
        self.stdout.write(
            f'Demo logins: demo_recruiter1 / demo_candidate1, password: {PASSWORD}'
        )